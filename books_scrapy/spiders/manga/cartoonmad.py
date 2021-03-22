import scrapy
import os
import re

from books_scrapy.items import Image
from books_scrapy.items import Manga
from books_scrapy.items import MangaChapter
from books_scrapy.spiders import Spider
from books_scrapy.utils import *
from scrapy import Request


class CartoonMadSpider(Spider):
    name = "www.cartoonmad.com"
    base_url = "https://www.cartoonmad.com"
    img_base_url = "https://www.cartoonmad.com/comic/comicpic.asp?file=/"
    start_urls = ["https://www.cartoonmad.com/comic/8113.html"]

    def get_book_info(self, response):
        name = response.css("title::text").get()[:-14].strip()

        tr_list = response.css("td:nth-child(2) tr:nth-child(4) tr:nth-child(2)")

        img_url = self.base_url + tr_list[1].css("img::attr(src)").get()
        file_path = get_img_store(self.settings, self.name, name)

        cover_image = Image(url=img_url, file_path=file_path)

        authors = (
            tr_list.css("tr:nth-child(5) td::text").get().strip()[6:].split(",")
        )
        categories = tr_list.css("tr:nth-child(3) a::text").get()
        # manga_excerpt = html.css("fieldset td::text").get().strip()
        excerpt = fmt_meta(fmt_label(response.xpath("//fieldset//td/text()").get()))

        return Manga(
            name=name,
            cover_image=cover_image,
            authors=authors,
            categories=categories,
            excerpt=excerpt,
            ref_url=response.url,
        )

    def get_book_catalog(self, response):
        book_catalog = []

        # response.css("fieldset")[1].css("tr > td")
        fieldset_list = response.xpath("//fieldset")
        if not fieldset_list:
            return book_catalog

        # td_list = fieldset_list[1].css("tr > td")
        td_list = fieldset_list[1].xpath(".//tr/td")
        for index, td in enumerate(td_list):
            # name = td.css("a::text").get()
            name = td.xpath(".//a/text()").get()
            
            # Skip empty html tag.
            # if not (td.css("a::attr(href)") and name):
            if not (td.xpath(".//a/@href") and name):
                continue

            try:
                # name.split(" ")[1]
                page_size = int(td.xpath(".//font/text()").get()[1:-2])

                # Get images store from settings.
                img_store = get_img_store(self.settings, self.name, manga_name, name)

                # Check whether file exists at `path` and file size equal to `c_page_size` to
                # skip duplicate download operation.
                if os.path.exists(img_store) and (page_size <= len(os.listdir(img_store))):
                    continue

                ref_url = self.base_url + td.xpath(".//a/@href").get()

                chapter = MangaChapter(
                    name=name,
                    ref_url=ref_url,
                    page_size=page_size,
                )

                book_catalog.append(chapter)
            except:
                # TODO: Error handling。
                continue
        
        return book_catalog

    def parse_chapter_data(self, html):
        # For now we only support asp hosted chapter.
        # urls = html.css("img::attr(src)").getall()
        original_img_urls = html.xpath("//img/@src").getall()
        filtered_img_urls = list(filter(lambda url: "/comicpic.asp?file=" in url, original_img_urls))
        if not filtered_img_urls:
            return

        chapter = revert_fmt_meta(html.meta)

        img_store = get_img_store(self.settings, self.name, chapter["rel_m_title"], chapter["name"])

        image_urls = []
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

            image_urls.append(image)

        chapter.image_urls = image_urls

        yield chapter