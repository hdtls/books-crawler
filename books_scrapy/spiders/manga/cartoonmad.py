from books_scrapy.items import *
from books_scrapy.loaders import ChapterLoader, MangaLoader
from books_scrapy.spiders import BookSpider


class CartoonMadSpider(BookSpider):
    name = "www.cartoonmad.com"

    def get_detail(self, response):
        loader = MangaLoader(response=response)

        loader.add_value("name", response.xpath("//title/text()").get().split(" - ")[0])
        loader.add_xpath("excerpt", "//fieldset//td/text()")
        loader.add_value("ref_urls", [response.url])
        loader.add_value(
            "cover_image",
            "https://www.cartoonmad.com/comic/comicpic.asp?file=/"
            + response.css(
                "td:nth-child(2) tr:nth-child(4) tr:nth-child(2) img::attr(src)"
            ).get(),
        )

        nested_loader = loader.nested_css("td:nth-child(2) tr:nth-child(4)")
        nested_loader.add_css("categories", "tr:nth-child(14) a::text")
        nested_loader.add_css(
            "authors", "tr:nth-child(2) tr:nth-child(5) td::text", re=r"原創作者： (.*)"
        )

        return loader.load_item()

    def get_catalog(self, response):
        return response.xpath("//fieldset//tr/td//a")

    def parse_chapter_data(self, response, book_info):
        # For now we only support asp hosted chapter.
        # urls = html.css("img::attr(src)").getall()
        img_url = response.xpath(
            "//img[contains(@src, '/comicpic.asp?file=')]/@src"
        ).get()

        if not img_url:
            # Only support asp query url.
            return

        page_size = list(
            filter(
                lambda p: p.isdigit(),
                response.xpath("//a[@class='pages']/text()").getall(),
            )
        ).pop()

        page_size = int(page_size)

        loader = ChapterLoader(response=response)

        loader.add_value("name", response.xpath("//title/text()").get().split(" - ")[1])
        loader.add_value("ref_urls", [response.url])
        loader.add_value(
            "assets",
            list(
                map(
                    lambda page: img_url[:-3] + str(page + 1).zfill(3),
                    range(page_size),
                )
            ),
        )

        item = loader.load_item()
        item.manga = book_info
        yield item
