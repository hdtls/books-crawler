import scrapy
import os
import re
from books_scrapy.items import Image
from books_scrapy.items import Manga
from books_scrapy.items import MangaChapter
from books_scrapy.utils import fmt_label
from scrapy import Request

class CartoonMadSpider(scrapy.Spider):
    name = "cartoonmad"
    base_url = "https://www.cartoonmad.com"
    start_urls = ["https://www.cartoonmad.com/comic/5292.html"]
    _invalid_id_list = ["2500"]

    custom_settings = {"MEDIA_ALLOW_REDIRECTS": True}

    def start_requests(self):
        for url in self.start_urls:
            # Handling missing chapters.
            if url.split("/")[-1].split(".")[0] in self._invalid_id_list:
                continue
            yield Request(url, self.parse)

    def parse(self, html):
        return self.parse_detail_page(html)

    def parse_detail_page(self, html):
        manga = Manga()
        manga["name"] = html.css("title::text").get()[:-14].strip()

        tr_list = html.css("td:nth-child(2) tr:nth-child(4) tr:nth-child(2)")

        cover_image = Image()
        cover_image["name"] = "cover.jpg"
        cover_image["url"] = self.base_url + tr_list[1].css("img::attr(src)").get()
        cover_image["file_path"] = (
            self.get_img_store(manga["name"]) + "/" + cover_image["name"]
        )

        manga["cover_image"] = cover_image
        manga["authors"] = (
            tr_list.css("tr:nth-child(5) td::text").get().strip()[6:].split(",")
        )
        manga["categories"] = tr_list.css("tr:nth-child(3) a::text").get()
        manga["excerpt"] = html.css("fieldset td::text").get().strip()

        # FIXME: Yield manga
        # yield manga
        self.logger.debug(manga)

        td_list = html.css("fieldset")[1].css("tr > td")

        for index, td in enumerate(td_list):
            chapter = MangaChapter()
            # Skip empty html tag.
            if td.css("a::attr(href)") is None:
                continue

            chapter["name"] = td.css("a::text").get()
            if chapter["name"] is None:
                continue

            chapter["identifier"] = chapter["name"].split(" ")[1]

            parent_id = html.url.split("/")[-1].split(".")[0]
            page_size = 0
            # Handing page fault.
            if [parent_id] == "1893":
                if index == 0:
                    page_size = 11
                elif index == 1:
                    page_size = 21
            elif parent_id == "3908":
                if index == 0:
                    page_size = 11
            else:
                page_size = int(fmt_label(td.css("font::text").get())[1:-2])

            chapter["parent_id"] = parent_id
            chapter["parent_name"] = manga["name"]
            chapter["page_size"] = page_size
            chapter["ref_url"] = self.base_url + fmt_label(
                td.css("a::attr(href)").get()
            )

            # Get images store from settings.
            img_store = self.get_img_store(manga["name"], chapter["name"])

            # Check whether file exists at `path` and file size equal to `c_page_size` to
            # skip duplicate download operation.
            if os.path.exists(img_store) and (page_size == len(os.listdir(img_store))):
                continue

            yield Request(
                chapter["ref_url"],
                meta=chapter,
                callback=self.parse_chapter_page,
            )

    def parse_chapter_page(self, html):
        # Hard code ad fixing.
        if "漫畫讀取中" in html.text:
            pattern = """var link = '(.*?)';"""
            res = re.search(pattern, html.text)
            c_url = res[1]
            yield Request(c_url, meta=html.meta, callback=self.parse_chapter_page)
            return

        urls = html.css("img::attr(src)").getall()

        # https://www.cartoonmad.com/comic/comicpic.asp?file=/4695/000/001
        # https://www.cartoonmad.com/home75378/4695/000/001.jpg
        # https://www.cartoonmad.com/comic/comicpic.asp?file=/3080/001/001&rimg=1
        # https://web3.cartoonmad.com/home13712/3080/001/001.jpg

        img_url_parts = self._get_img_url_parts(urls)

        # Perform chapter download operation.
        # https://web.cartoonmad.com/c37sn562e81/3899/001/010.jpg
        # https://www.cartoonmad.com/comic/comicpic.asp?file=/8726/001/002

        chapter = html.meta

        img_store = self.get_img_store(chapter["parent_name"], chapter["name"])

        image_list = []
        for page in range(1, chapter["page_size"] + 1):
            image_name = str(page).zfill(4)

            http_headers = {
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
                "DNT": "1",
                "Host": "www.cartoonmad.com",
                "Referer": chapter["ref_url"],
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
            }

            url = (
                img_url_parts[0]
                + chapter["parent_id"]
                + "/"
                + chapter["identifier"]
                + "/"
                + image_name
                + img_url_parts[1]
            )

            image = Image(
                name=image_name + ".jpg",
                file_path=img_store,
                url=url,
                http_headers=http_headers,
            )

            image_list.append(image)

        chapter["image_urls"] = image_list

        # FIXME: Yield chapter
        yield chapter

    def _get_img_url_parts(self, urls):
        url_prefix = ""
        url_suff = ""

        # Placeholder image url list.
        p_urls = [
            "https://www.cartoonmad.com/image/rad1.gif",
            "https://www.cartoonmad.com/image/panen.png",
            "https://www.cartoonmad.com/image/rad.gif",
        ]

        for url in urls:
            if url in p_urls:
                # Skip invalid manga image url.
                continue
            if "cc.fun8.us" in url:
                # Skip invalid manga image url.
                continue
            if "comicpic.asp" in url:
                url_prefix = "https://www.cartoonmad.com/comic/comicpic.asp?file=/"
                if "&rimg=1" in url:
                    url_suff = "&rimg=1"
                break
            elif "cartoonmad" in url:
                url_splits = image_url.split("/")
                url_prefix = (
                    url_splits[0] + "//" + url_splits[2] + "/" + url_splits[3] + "/"
                )
                url_suff = ".jpg"
                break
        return [url_prefix, url_suff]

        image_list = []
        for page in range(1, chapter["page_size"] + 1):
            image_name = str(page).zfill(4)

            http_headers = {
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
                "DNT": "1",
                "Host": "www.cartoonmad.com",
                "Referer": chapter["ref_url"],
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
            }

            url = (
                url_prefix
                + chapter["parent_id"]
                + "/"
                + chapter["identifier"]
                + "/"
                + image_name
                + url_suff
            )

            image = Image(
                name=image_name + ".jpg",
                file_path=img_store + "/" + image_name + ".jpg",
                url=url,
                http_headers=http_headers,
            )

            image_list.append(image)
        return image_list

    def get_img_store(self, name, chapter_name=None):
        fragments = [self.settings["IMAGES_STORE"], self.name]
        if name is not None:
            fragments.append(name)

        if chapter_name is not None:
            fragments.append(chapter_name)

        return "/".join(fragments)