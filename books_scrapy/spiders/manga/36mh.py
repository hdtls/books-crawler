from books_scrapy.loaders import MangaChapterLoader, MangaLoader
from books_scrapy.items import *
from books_scrapy.utils import *
from books_scrapy.spiders import BookSpider


class The36MHSpider(BookSpider):
    name = "www.36mh.net"

    def get_book_info(self, response):
        loader = MangaLoader(response=response)
        loader.context["refer"] = self.name

        loader.add_xpath("name", "//div[contains(@class, 'book-title')]//span/text()")
        loader.add_xpath("excerpt", "//div[@id='intro-all']//p/text()")
        loader.add_value(
            "cover_image",
            list(
                map(
                    self._parse_img_url,
                    response.xpath(
                        "//div[contains(@class, 'book-cover')]/p/img/@src"
                    ).getall(),
                )
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

    def _parse_img_url(self, url):
        if not "//" in url:
            # Invalid image url.
            return None

        host = url.split("//")[1].split("/")[0]
        if host in [
            "img001.1fi4b.cn",
            "img001.shmkks.com",
            "img001.pkqiyi.com",
            "img001.sdldcy.com",
            "img001.microland-design.com",
        ]:
            return url.replace(host, "img001.36man.cc")
        return url

    def get_book_catalog(self, response):
        return response.xpath("//ul[@id='chapter-list-4']/li/a")

    def parse_chapter_data(self, response):
        img_name_list = eval_js_variable("chapterImages", response.text)

        path = eval_js_variable("chapterPath", response.text)

        if not (img_name_list and path):
            return

        loader = MangaChapterLoader(response=response)

        loader.add_xpath("name", "//div[contains(@class, 'w996 title pr')]/h2/text()")
        loader.add_value("books_query_id", revert_formatted_meta(response.meta))
        loader.add_value("ref_urls", [response.url])
        loader.add_value(
            "image_urls",
            list(
                map(
                    lambda url: "https://img001.microland-design.com/" + path + url,
                    img_name_list,
                )
            ),
        )

        yield loader.load_item()