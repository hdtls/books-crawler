import scrapy
import os
import re
import json

from books_scrapy.items import Image
from books_scrapy.items import Manga
from books_scrapy.items import MangaChapter
from books_scrapy.utils import *
from scrapy import Request


class The36MHSpider(scrapy.Spider):
    name = "36mh"
    base_url = "https://www.36mh.net"
    img_base_url = "https://img001.microland-design.com"
    start_urls = [
        # "https://www.36mh.net/list/update/",
        "https://www.36mh.net/manhua/jiesuomoshide99genvzhu/",
        # "https://www.36mh.net/manhua/jiesuomoshide99genvzhu/790041.html#p=1",/
    ]

    def parse(self, html):
        return self.parse_detail_page(html)

    def parse_detail_page(self, html):
        manga_name = fmt_label(
            html.xpath("//div[contains(@class, 'book-title')]//span/text()").get()
        )

        manga_intro = fmt_label(html.xpath("//div[@id='intro-all']//p/text()").get())

        img_name = "cover.jpg"
        img_url = fmt_label(
            html.xpath("//div[contains(@class, 'book-cover')]/p/img/@src").get()
        )
        img_file_path = get_img_store(self.settings, self.name, manga_name)

        manga_cover_image = Image(name=img_name, url=img_url, file_path=img_file_path)

        for span in html.xpath("//ul[contains(@class, 'detail-list')]//span"):
            label = span.xpath("./strong/text()").get()
            text = span.xpath("./a/text()").get()
            if label == "漫画地区：":
                manga_area = text
            elif label == "字母索引：":
                index = text
            elif label == "漫画剧情：":
                manga_categories = span.xpath("./a/text()").getall()
            elif label == "漫画作者：":
                manga_authors = fmt_label(text).split(",")
            elif label == "漫画状态：":
                manga_status = text

        manga = Manga(
            name=manga_name,
            cover_image=manga_cover_image,
            status=manga_status,
            authors=manga_authors,
            excerpt=manga_intro,
            categories=manga_categories,
            area=manga_area,
            ref_url=html.url,
        )

        yield manga

        for li in html.xpath("//ul[@id='chapter-list-4']/li"):
            manga_chapter_id = fmt_label(li.xpath("./a/@href").get())
            manga_chapter_name = fmt_label(li.xpath(".//span/text()").get())
            manga_chapter_ref_url = self.base_url + manga_chapter_id

            chapter = MangaChapter(
                identifier=manga_chapter_id,
                name=manga_chapter_name,
                ref_url=manga_chapter_ref_url,
                parent_id=html.url,
                parent_name=manga_name,
            )

            yield Request(
                manga_chapter_ref_url, self.parse_chapter_page, meta=fmt_meta(chapter)
            )

    def parse_chapter_page(self, html):
        url_suffix_match = re.findall(r"var chapterImages = (.*?);", html.text)
        path_match = re.findall(r"var chapterPath = (.*?);", html.text)

        if not url_suffix_match or not path_match:
            return

        img_list = []

        for index, url in enumerate(json.loads(url_suffix_match[0])):
            img_url = self.img_base_url + "/" + json.loads(path_match[0]) + url
            img_name = str(index + 1).zfill(4) + ".jpg"
            img_file_path = get_img_store(
                self.settings,
                self.name,
                revert_fmt_meta(html.meta)["parent_name"],
                revert_fmt_meta(html.meta)["name"],
            )
            image = Image(
                url=img_url, name=img_name, file_path=img_file_path, http_headers=None
            )
            img_list.append(image)

        chapter = MangaChapter(revert_fmt_meta(html.meta))
        chapter["image_urls"] = img_list
        chapter["page_size"] = len(img_list)

        yield chapter