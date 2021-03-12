import scrapy
import os
import re

from books_scrapy.items import Image
from books_scrapy.items import Manga
from books_scrapy.items import MangaChapter
from books_scrapy.utils import *
from scrapy import Request


class CartoonMadSpider(scrapy.Spider):
    name = "cartoonmad"
    base_url = "https://www.cartoonmad.com"
    img_base_url = "https://www.cartoonmad.com/comic/comicpic.asp?file=/"
    start_urls = ["https://www.cartoonmad.com/comic/8113.html"]

    custom_settings = {"MEDIA_ALLOW_REDIRECTS": True}

    def parse(self, html):
        return self.parse_detail_page(html)

    def parse_detail_page(self, html):
        manga_name = html.css("title::text").get()[:-14].strip()

        tr_list = html.css("td:nth-child(2) tr:nth-child(4) tr:nth-child(2)")

        img_name = "cover.jpg"
        img_url = self.base_url + tr_list[1].css("img::attr(src)").get()
        img_file_path = get_img_store(self.settings, self.name, manga_name)

        manga_cover_image = Image(name=img_name, url=img_url, file_path=img_file_path)

        manga_authors = (
            tr_list.css("tr:nth-child(5) td::text").get().strip()[6:].split(",")
        )
        manga_categories = tr_list.css("tr:nth-child(3) a::text").get()
        # manga_excerpt = html.css("fieldset td::text").get().strip()
        manga_excerpt = fmt_meta(fmt_label(html.xpath("//fieldset//td/text()").get()))

        yield Manga(
            name=manga_name,
            alias=None,
            background_image=None,
            cover_image=manga_cover_image,
            promo_image=None,
            authors=manga_authors,
            status=None,
            categories=manga_categories,
            excerpt=manga_excerpt,
            area=None,
            ref_url=html.url,
        )

        # Table of contents
        # html.css("fieldset")[1].css("tr > td")
        fieldset_list = html.xpath("//fieldset")
        if not fieldset_list:
            return

        # td_list = fieldset_list[1].css("tr > td")
        td_list = fieldset_list[1].xpath(".//tr/td")
        for index, td in enumerate(td_list):
            # manga_chapter_name = td.css("a::text").get()
            manga_chapter_name = td.xpath(".//a/text()").get()
            
            # Skip empty html tag.
            # if not (td.css("a::attr(href)") and manga_chapter_name):
            if not (td.xpath(".//a/@href") and manga_chapter_name):
                continue

            try:
                # manga_chapter_name.split(" ")[1]
                page_size = int(td.xpath(".//font/text()").get()[1:-2])

                # Get images store from settings.
                img_store = get_img_store(self.settings, self.name, manga_name, manga_chapter_name)

                # Check whether file exists at `path` and file size equal to `c_page_size` to
                # skip duplicate download operation.
                if os.path.exists(img_store) and (page_size <= len(os.listdir(img_store))):
                    continue

                ref_url = self.base_url + td.xpath(".//a/@href").get()

                chapter = MangaChapter(
                    name=manga_chapter_name,
                    ref_url=ref_url,
                    page_size=page_size,
                    rel_m_id=html.url,
                    rel_m_title=manga_name
                )

                yield Request(
                    ref_url,
                    meta=fmt_meta(chapter),
                    callback=self.parse_chapter_page,
                )
            except:
                # TODO: Error handling。
                continue

    def parse_chapter_page(self, html):
        # For now we only support asp hosted chapter.
        # urls = html.css("img::attr(src)").getall()
        original_img_urls = html.xpath("//img/@src").getall()
        filtered_img_urls = list(filter(lambda url: "/comicpic.asp?file=" in url, original_img_urls))
        if not filtered_img_urls:
            return

        chapter = revert_fmt_meta(html.meta)

        img_store = get_img_store(self.settings, self.name, chapter["rel_m_title"], chapter["name"])

        image_list = []
        for page in range(1, chapter["page_size"] + 1):
            img_name = str(page).zfill(4) + ".jpg"
            img_url =  filtered_img_urls[0]

            # Replace page identifier.
            if "?" in img_url:
                img_url = img_url.split("?")[0][:-3] + str(page).zfill(3) + img_url.split("?")[1]
            else:
                img_url = img_url[:-3] + str(page).zfill(3)

            http_headers = {
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
                "DNT": "1",
                "Host": "www.cartoonmad.com",
                "Referer": html.url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
            }

            image = Image(
                name=img_name,
                file_path=img_store,
                url=img_url,
                http_headers=http_headers,
            )

            image_list.append(image)

        chapter["image_urls"] = image_list

        yield chapter