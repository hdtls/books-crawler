import os

from books_scrapy.items import *
from books_scrapy.spiders import Spider
from books_scrapy.utils import *


class CartoonMadSpider(Spider):
    name = "www.cartoonmad.com"
    base_url = "https://www.cartoonmad.com"
    img_base_url = "https://www.cartoonmad.com/comic/comicpic.asp?file=/"
    start_urls = ["https://www.cartoonmad.com/comic/8113.html"]

    def get_book_info(self, response):
        name = response.css("title::text").get()[:-14].strip()

        tr_list = response.css("td:nth-child(2) tr:nth-child(4) tr:nth-child(2)")

        img_url = self.base_url + tr_list[1].css("img::attr(src)").get()

        cover_image = dict(url=img_url)

        authors = tr_list.css("tr:nth-child(5) td::text").get().strip()[6:].split(",")
        categories = tr_list.css("tr:nth-child(3) a::text").get()
        # manga_excerpt = html.css("fieldset td::text").get().strip()
        excerpt = fmt_meta(fmt_label(response.xpath("//fieldset//td/text()").get()))

        return Manga(
            name=name,
            cover_image=cover_image,
            authors=authors,
            categories=categories,
            excerpt=excerpt,
            ref_urls=[response.url],
        )

    def get_book_catalog(self, response):
        return response.xpath("//fieldset//tr/td//a")

    def parse_chapter_data(self, response):
        # For now we only support asp hosted chapter.
        # urls = html.css("img::attr(src)").getall()
        img_url = response.xpath(
            "//img[contains(@src, '/comicpic.asp?file=')]/@src"
        ).get()

        page_size = list(
            filter(
                lambda p: p.isdigit(),
                response.xpath("//a[@class='pages']/text()").getall(),
            )
        ).pop()
        page_size = int(page_size)

        if not img_url:
            # Only support asp query url.
            return

        image_urls = []

        for page in range(1, page_size + 1):
            img_name = str(page).zfill(4) + ".jpg"
            img_url = img_url[:-3] + str(page).zfill(3)

            image = dict(
                name=img_name,
                url=img_url,
            )

            image_urls.append(image)

        chapter = MangaChapter(
            name=response.xpath("//title/text()").get().split(" - ")[1],
            books_query_id=revert_fmt_meta(response.meta),
            ref_urls=[response.url],
            image_urls=image_urls,
        )

        yield chapter