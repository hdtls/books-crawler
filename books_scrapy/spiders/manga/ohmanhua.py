import base64
import demjson
import re

from books_scrapy.items import *
from books_scrapy.utils import *
from books_scrapy.spiders import Spider
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class OHManhuaSpider(Spider):
    name = "www.cocomanhua.com"
    base_url = "https://www.cocomanhua.com"
    start_urls = [
        "https://www.cocomanhua.com/10129/",
    ]

    def get_book_info(self, response):
        # name = html.css("dd.fed-deta-content h1::text").get()
        name = response.xpath(
            "//dd[contains(@class, 'fed-deta-content')]/h1/text()"
        ).get()

        # img_url = html.css("dt.fed-deta-images a::attr(data-original)").get()
        img_url = response.xpath(
            "//dt[contains(@class, 'fed-deta-images')]/a/@data-original"
        ).get()
        file_path = get_img_store(self.settings, self.name, name)

        cover_image = Image(url=img_url, file_path=file_path)

        area = None
        alias = None
        status = None
        authors = []
        categories = None
        excerpt = ""
        # html.css("dd.fed-deta-content ul li")
        for li in response.xpath("//dd[contains(@class, 'fed-deta-content')]/ul/li"):
            # label = li.css("span::text").get()
            label = li.xpath(".//span/text()").get()
            # text = li.css("a::text").get()
            text = li.xpath("./a/text()").get()
            if label == "别名":
                # There is an empty " " in results that should be ignored.
                alias = list(
                    filter(lambda str: str != " ", li.xpath("./text()").getall())
                )
                alias = fmt_label(alias[0]) if len(alias) >= 1 else ""
                alias = alias.split(",")
            elif label == "状态":
                # status = text
                status = text
            elif label == "作者":
                if text.startswith("作者:"):
                    text = fmt_label(text[3:])
                if " " in text:
                    authors = text.split(" ")
                elif "x" in text:
                    authors = text.split("x")
                else:
                    authors = [text]
            elif label == "类别":
                # categories = li.css("a::text").getall()
                categories = li.xpath("./a/text()").getall()
            elif label == "简介":
                # excerpt = li.css("div::text").get()
                excerpt = li.xpath("./div/text()").get()

        return Manga(
            name=name,
            alias=alias,
            cover_image=cover_image,
            authors=authors,
            status=status,
            categories=categories,
            excerpt=excerpt,
            area=area,
            ref_url=response.url,
        )

    def get_book_catalog(self, response):
        return response.xpath("//div[contains(@class, 'all_data_list')]//li/a")

    def parse_chapter_data(self, response):
        match = re.findall(r"var C_DATA= ?(.*?);", response.text)

        if len(match) <= 0:
            return

        loaded_chapter = self._load_chapter(demjson.decode(match[0]))

        if not loaded_chapter:
            return

        name = loaded_chapter["pagename"]
        page_size = loaded_chapter["page_size"]

        image_urls = []
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
            )
            image_urls.append(image)

        chapter = MangaChapter(
            name=name,
            book_id=revert_fmt_meta(response.meta),
            ref_url=response.url,
            image_urls=image_urls,
        )

        yield chapter

    @staticmethod
    def _load_chapter(ciphertext):
        assert isinstance(ciphertext, str)

        plaintext = OHManhuaSpider._decrypt(ciphertext)

        match = re.findall(r"mh_info=(.*?);", plaintext)

        if not match:
            return None

        # If matched then serializing first match to original chapter dict value.
        dict_value = demjson.decode(match[0])

        if dict_value["enc_code1"]:
            dict_value["page_size"] = int(
                fmt_label(OHManhuaSpider._decrypt(dict_value["enc_code1"]))
            )

        if dict_value["enc_code2"]:
            dict_value["img_url_path"] = OHManhuaSpider._decrypt(
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

    @staticmethod
    def _decrypt(ciphertext, key=None):
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