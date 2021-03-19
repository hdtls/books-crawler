import scrapy
import os
import re
import json

from books_scrapy.items import *
from books_scrapy.utils import *
from books_scrapy.spiders import Spider
from scrapy import Request


class The36MHSpider(Spider):
    name = "www.36mh.net"
    base_url = "https://www.36mh.net"
    img_base_url = "https://img001.microland-design.com"
    start_urls = [
        "https://www.36mh.net/manhua/nvzixueyuandenansheng/"
    ]

    def get_book_info(self, response):
        name = response.xpath("//div[contains(@class, 'book-title')]//span/text()").get()
        
        excerpt = fmt_label(response.xpath("//div[@id='intro-all']//p/text()").get())

        cover_image = Image(
            url=response.xpath(
                "//div[contains(@class, 'book-cover')]/p/img/@src"
            ).get(),
            file_path=get_img_store(self.settings, self.name, name),
        )

        for span in response.xpath("//ul[contains(@class, 'detail-list')]//span"):
            label = span.xpath("./strong/text()").get()
            text = span.xpath("./a/text()").get()
            if label == "漫画地区：":
                area = text
            elif label == "字母索引：":
                index = text
            elif label == "漫画剧情：":
                categories = span.xpath("./a/text()").getall()
            elif label == "漫画作者：":
                authors = fmt_label(text).split(",")
            elif label == "漫画状态：":
                status = text

        # TODO: Manga alias serializng if have.
        return Manga(
            name=name,
            cover_image=cover_image,
            authors=authors,
            status=status,
            categories=categories,
            excerpt=excerpt,
            area=area,
            ref_url=response.url,
        )

    def get_book_catalog(self, response):
        book_catalog = []

        for li in response.xpath("//ul[@id='chapter-list-4']/li"):
            manga_chapter_id = fmt_label(li.xpath("./a/@href").get())
            manga_chapter_name = fmt_label(li.xpath(".//span/text()").get())
            manga_chapter_ref_url = self.base_url + manga_chapter_id

            chapter = MangaChapter(
                name=manga_chapter_name,
                ref_url=manga_chapter_ref_url,
                rel_m_id=response.url,
                rel_m_title=manga_name,
            )

            book_catalog.append(chapter)

        return book_catalog

    def parse_chapter_data(self, response):
        img_name_list = eval_js_variable("chapterImages", response.text)

        path = eval_js_variable("chapterPath", response.text)

        if not (img_name_list and path):
            return

        chapter = revert_fmt_meta(response.meta)

        image_urls = []

        for index, url in enumerate(img_name_list):
            img_url = self.img_base_url + "/" + path + url
            img_name = str(index + 1).zfill(4) + ".jpg"
            file_path = get_img_store(
                self.settings,
                self.name,
                chapter.rel_m_title,
                chapter.name,
            )
            image = Image(
                url=img_url, name=img_name, file_path=file_path
            )
            image_urls.append(image)

        chapter.image_urls = image_urls

        yield chapter