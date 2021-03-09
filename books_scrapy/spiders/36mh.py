import scrapy
import os
import re
import json

from books_scrapy.items import Image
from books_scrapy.items import Manga
from books_scrapy.items import MangaChapter
from books_scrapy.utils import fmt_label
from books_scrapy.utils import get_img_store
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
        manga = Manga()

        manga["name"] = html.xpath(
            "//div[contains(@class, 'book-title')]//span/text()"
        ).get()
        manga["excerpt"] = html.xpath("//div[@id='intro-all']//p/text()").get().strip()

        cover_image = Image()
        cover_image["name"] = "cover.jpg"
        cover_image["url"] = html.xpath(
            "//div[contains(@class, 'book-cover')]/p/img/@src"
        ).get()
        cover_image["file_path"] = get_img_store(
            self.settings, self.name, manga["name"]
        )

        for span in html.xpath("//ul[contains(@class, 'detail-list')]//span"):
            label = span.xpath("./strong/text()").get()
            text = span.xpath("./a/text()").get()
            if label == "漫画地区：":
                manga["area"] = text
            elif label == "字母索引：":
                index = text
            elif label == "漫画剧情：":
                manga["categories"] = span.xpath("./a/text()").getall()
            elif label == "漫画作者：":
                manga["authors"] = fmt_label(text).split(",")
            elif label == "漫画状态：":
                manga["status"] = text

        for li in html.xpath("//ul[@id='chapter-list-4']/li"):
            chapter = MangaChapter()
            chapter["name"] = li.xpath("//span/text()").get().strip()
            chapter["ref_url"] = self.base_url + fmt_label(li.xpath("./a/@href").get())
            chapter["parent_id"] = html.url
            chapter["parent_name"] = manga["name"]
            yield Request(chapter["ref_url"], self.parse_chapter_page, meta=chapter)

    def parse_chapter_page(self, html):
        chapter = html.meta

        url_suffix_match = re.findall(r"var chapterImages = (.*?);", html.text)
        path_match = re.findall(r"var chapterPath = (.*?);", html.text)

        if not url_suffix_match or not path_match:
            return

        image_list = []

        for index, url in enumerate(json.loads(url_suffix_match[0])):
            image = Image()
            image["url"] = self.img_base_url + "/" + json.loads(path_match[0]) + url
            image["name"] = str(index).zfill(4) + ".jpg"
            image["file_path"] = get_img_store(
                self.settings, self.name, chapter["parent_name"], image["name"]
            )

            image_list.append(image)

        chapter["image_urls"] = image_list
        
        yield chapter