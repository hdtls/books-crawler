import base64
import demjson
import scrapy
import re
import os

from books_scrapy.items import Manga
from books_scrapy.items import MangaChapter
from books_scrapy.items import Image
from books_scrapy.utils import *
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from pathlib import Path
from scrapy import Request


class OHManhuaSpider(scrapy.Spider):
    name = "ohmanhua"
    base_url = "https://www.cocomanhua.com"
    start_urls = [
        # "https://www.cocomanhua.com/show?orderBy=update",
        # "https://www.cocomanhua.com/18865/",
        "https://www.cocomanhua.com/18865/1/17.html"
    ]

    def start_requests(self):
        for url in self.start_urls:
            if "?" in url:
                yield Request(url, self.parse)
            elif url.endswith(".html"):
                yield Request(url, self.parse_chapter_page)
            elif url.endswith("/"):
                yield Request(url, self.parse_detail_page)

    def parse(self, html):
        # return self.parse_detail_page(html)
        return self.parse_chapter_page(html)

    def parse_detail_page(self, html):
        # manga_name = html.css("dd.fed-deta-content h1::text").get()
        manga_name = html.xpath(
            "//dd[contains(@class, 'fed-deta-content')]/h1/text()"
        ).get()

        img_name = "cover.jpg"
        # img_url = html.css("dt.fed-deta-images a::attr(data-original)").get()
        img_url = html.xpath(
            "//dt[contains(@class, 'fed-deta-images')]/a/@data-original"
        ).get()
        img_file_path = get_img_store(self.settings, self.name, manga_name)

        manga_cover_image = Image(
            name=img_name, url=img_url, file_path=img_file_path, http_headers=None
        )

        manga_area = "中国大陆"
        # html.css("dd.fed-deta-content ul li")
        for li in html.xpath("//dd[contains(@class, 'fed-deta-content')]/ul/li"):
            # label = li.css("span::text").get()
            label = li.xpath(".//span/text()").get()
            # text = li.css("a::text").get()
            text = li.xpath("./a/text()").get()
            if label == "别名":
                # There is an empty " " in results that should be ignored.
                manga_alias = list(
                    filter(lambda str: str != " ", li.xpath("./text()").getall())
                )
                manga_alias = fmt_label(manga_alias[0]) if len(manga_alias) >= 1 else ""
                manga_alias = manga_alias.split(",")
            elif label == "状态":
                # manga_status = text
                manga_status = text
            elif label == "作者":
                if text.startswith("作者:"):
                    text = fmt_label(text[3:])
                if " " in text:
                    manga_authors = text.split(" ")
                elif "x" in text:
                    manga_authors = text.split("x")
                else:
                    manga_authors = [text]
            elif label == "类别":
                # manga_categories = li.css("a::text").getall()
                manga_categories = li.xpath("./a/text()").getall()
            elif label == "简介":
                # manga_intro = li.css("div::text").get()
                manga_intro = li.xpath("./div/text()").get()

        yield Manga(
            name=manga_name,
            alias=manga_alias,
            background_image=None,
            cover_image=manga_cover_image,
            promo_image=None,
            authors=manga_authors,
            status=manga_status,
            categories=manga_categories,
            excerpt=manga_intro,
            area=manga_area,
            ref_url=html.url,
        )

        # Capter list serializing.
        # html.css("div.all_data_list li")
        for li in html.xpath("//div[contains(@class, 'all_data_list')]//li"):
            # name = fmt_label(li.css("a::text").get()
            name = fmt_label(li.xpath("./a/text()").get())

            # url = self.base_url + li.css("a::attr(href)").get()
            url = self.base_url + li.xpath("./a/@href").get()

            # TODO: Add detect to check whether chapter already downloaded.
            yield Request(url, self.parse_chapter_page, meta=fmt_meta(html.url))

    def parse_chapter_page(self, html):
        match = re.findall(r"var C_DATA= ?(.*?);", html.text)

        if len(match) <= 0:
            return

        loaded_chapter = self._load_chapter(demjson.decode(match[0]))

        if not loaded_chapter:
            return

        manga_name = loaded_chapter["mhname"]
        name = loaded_chapter["pagename"]
        page_size = loaded_chapter["page_size"]
        img_store = get_img_store(self.settings, self.name, manga_name, name)

        # Download only when `page_size` is valid
        # and the number of files in the folder `img_store` is less than page_size.
        if not page_size or len(os.listdir(img_store)) >= page_size:
            return

        img_list = []
        base_url = (
            "https://"
            + loaded_chapter["domain"]
            + "/comic/"
            + loaded_chapter["img_url_path"]
        )

        for img_index in range(page_size):
            img_url = (
                base_url
                + str(int(loaded_chapter["startimg"]) + img_index).zfill(4)
                + ".jpg"
            )
            img_name = str(img_index).zfill(4) + ".jpg"
            image = Image(
                name=img_name,
                url=img_url,
                file_path=get_img_store(self.settings, self.name, manga_name, name),
                http_headers=None,
            )
            img_list.append(image)

        yield MangaChapter(
            name=name,
            ref_url=html.url,
            image_urls=img_list,
            page_size=page_size,
            rel_m_id=revert_fmt_meta(html.meta),
            rel_m_title=manga_name
        )

    def _load_chapter(self, ciphertext):
        assert isinstance(ciphertext, str)

        plaintext = self._decrypt(ciphertext)

        match = re.findall(r"mh_info=(.*?);", plaintext)

        if not match:
            return None

        # If matched then serializing first match to original chapter dict value.
        dict_value = demjson.decode(match[0])

        if dict_value["enc_code1"]:
            dict_value["page_size"] = int(
                fmt_label(self._decrypt(dict_value["enc_code1"]))
            )

        if dict_value["enc_code2"]:
            dict_value["img_url_path"] = self._decrypt(
                dict_value["enc_code2"],
                "fw125gjdi9ertyui",
            )

        """
        {
            startimg:1,
            enc_code1:"dGEvZnplRWVIZWFnMTNPMjdCWm1EQT09",
            mhid:"18865",
            enc_code2:"WTl1dTAwQ2FVTnBjOGRKcmlwRERQZndSTFFkalpjNVpSYzlYTFJidExwZHJLNDZVa2pHRk16Y1BVRnpHaXpHSDl6N1hpWmR4dUszdzZmVi9xc0FDZkpobkwyWWx4ank3c0tCZ3ZDUk05c1k9",
            mhname:"恶魔X天使 不能友好相处",
            pageid:3259298,
            pagename:"015 见义勇为的天使",
            pageurl:"1/17.html",
            readmode:3,
            maxpreload:5,
            defaultminline:1,
            domain:"img.cocomanhua.com",
            manga_size:"",
            default_price:0,
            price:0,

            page_size:36,
            img_url_path:"18865/eGJhNUxPeVN6S0pheHYyNVhmUk51NTV1ZS8xOFc0c09WUE84bG14ZE9wST0=/"
        }
        """
        return dict_value

    def _decrypt(self, ciphertext, key=None):
        ciphertext = base64.b64decode(ciphertext)
        input_key = key.encode("utf-8") if key else None

        # var __READKEY = "JRUIFMVJDIWE569j"
        # var __READKEY = "fw12558899ertyui"
        # var __READKEY = 'fw122587mkertyui';
        default_key_list = [
            b"fw122587mkertyui",
            b"fw12558899ertyui",
            b"JRUIFMVJDIWE569j",
        ]

        if input_key:
            default_key_list.insert(0, input_key)

        for k in default_key_list:
            # Encode key to utf8 bytes.
            message = base64.b64decode(ciphertext)

            decryptor = Cipher(algorithms.AES(k), modes.ECB()).decryptor()
            # PKCS7 unpadding
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

            plaintext = decryptor.update(message) + decryptor.finalize()
            plaintext = unpadder.update(plaintext) + unpadder.finalize()

            if plaintext:
                # Convert bytes to utf8 string.
                return plaintext.decode()

        return ciphertext.decode()