from books_scrapy.items import *
from books_scrapy.utils import *
from books_scrapy.spiders import Spider


class The36MHSpider(Spider):
    name = "www.36mh.net"
    base_url = "https://www.36mh.net"
    img_base_url = "https://img001.microland-design.com"
    start_urls = ["https://www.36mh.net/manhua/nvzixueyuandenansheng/"]

    def get_book_info(self, response):
        name = response.xpath(
            "//div[contains(@class, 'book-title')]//span/text()"
        ).get()

        excerpt = fmt_label(response.xpath("//div[@id='intro-all']//p/text()").get())

        cover_image = Image(
            url=response.xpath("//div[contains(@class, 'book-cover')]/p/img/@src").get()
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
        return response.xpath("//ul[@id='chapter-list-4']/li/a")

    def parse_chapter_data(self, response):
        img_name_list = eval_js_variable("chapterImages", response.text)

        path = eval_js_variable("chapterPath", response.text)

        if not (img_name_list and path):
            return

        name = response.xpath(
            "//div[contains(@class, 'w996 title pr')]/h2/text()"
        ).get()

        image_urls = []

        for index, url in enumerate(img_name_list):
            image = Image(
                url=self.img_base_url + "/" + path + url,
                name=str(index + 1).zfill(4) + ".jpg",
            )
            image_urls.append(image)

        chapter = MangaChapter(
            name=name,
            book_id=revert_fmt_meta(response.meta),
            ref_url=response.url,
            image_urls=image_urls,
        )

        yield chapter