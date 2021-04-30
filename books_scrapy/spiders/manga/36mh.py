from scrapy.loader import ItemLoader
from books_scrapy.spiders import BookSpider
import json
import re

from books_scrapy.items import *
from books_scrapy.loaders import ChapterLoader, MangaLoader
from books_scrapy.utils.misc import (
    eval_js_variable,
    formatted_meta,
    revert_formatted_meta,
)


class The36MHSpider(BookSpider):
    name = "www.36mh.net"
    # start_urls = ["https://www.36mh.net/manhua/jiesuomoshide99genvzhu/"]

    def get_detail(self, response):
        loader = MangaLoader(response=response)

        loader.add_xpath("name", "//div[contains(@class, 'book-title')]//span/text()")
        loader.add_xpath("excerpt", "//div[@id='intro-all']//p/text()")
        loader.add_value(
            "cover_image",
            self._replace_img_url_hostname(
                response.xpath("//div[contains(@class, 'book-cover')]/p/img/@src").get()
            ),
        )
        loader.add_value("ref_urls", [response.url])

        for span in response.xpath("//ul[contains(@class, 'detail-list')]//span"):
            label = span.xpath("./strong/text()").get()
            text = span.xpath("./a/text()").get()
            if label == "漫画地区：":
                loader.add_value("area", text)
            elif label == "漫画剧情：":
                loader.add_value("categories", span.xpath("./a/text()").getall())
            elif label == "漫画作者：":
                loader.add_value("authors", text)
            elif label == "漫画状态：":
                loader.add_value("schedule", text)

        return loader.load_item()

    def get_catalog(self, response):
        return response.xpath("//ul[@id='chapter-list-4']/li/a")

    def parse_chapter_data(self, response, user_info):
        image_urls = eval_js_variable("chapterImages", response.text)

        path = eval_js_variable("chapterPath", response.text)

        if not (image_urls and path):
            return

        image_urls = list(map(lambda url: path + url, image_urls))

        loader = ChapterLoader(response=response)

        loader.add_xpath("name", "//div[contains(@class, 'w996 title pr')]/h2/text()")
        loader.add_value("books_query_id", user_info)
        loader.add_value("ref_urls", [response.url])
        loader.add_value("assets", image_urls)

        item = loader.load_item()

        yield response.follow(
            "/js/config.js",
            self._resolve_img_url_hostname,
            meta=formatted_meta(item),
            dont_filter=True,
        )

    def _resolve_img_url_hostname(self, response):
        """
        Resolve image url hostname
        see /js/config.js for more detail.
        """

        # Add prefix ' ' to ignore '//resHost'
        matches = re.findall(r" resHost: ?(.*),", response.text)
        if not matches:
            return

        match = json.loads(matches[0])
        if not match:
            return

        domain = match[0].get("domain")
        if not domain:
            return

        domain = domain[0]

        item = revert_formatted_meta(response.meta)

        files = []
        for image in item.assets.files:
            image["ref_url"] = domain + image["ref_url"]
            files.append(image)

        item.assets.files = files

        yield item

    def _replace_img_url_hostname(self, url):
        """
        Replace image url hostname with specified value
        see: /js/common.js for more detail.
        """
        if not "//" in url:
            # Invalid image url.
            return None

        host = url.split("//")[1].split("/")[0]
        orig_img_hosts = [
            "img001.1fi4b.cn",
            "img001.shmkks.com",
            "img001.pkqiyi.com",
            "img001.sdldcy.com",
            "img001.microland-design.com",
        ]
        if host in orig_img_hosts:
            return url.replace(host, "img001.36man.cc")
        return url
