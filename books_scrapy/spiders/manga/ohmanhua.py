import base64
import demjson
import re

from books_scrapy.items import *
from books_scrapy.loaders import MangaChapterLoader, MangaLoader
from books_scrapy.spiders import BookSpider
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class OHManhuaSpider(BookSpider):
    name = "www.cocomanhua.com"

    def get_detail(self, response):
        loader = MangaLoader(response=response)
        loader.add_xpath("name", "//dd[contains(@class, 'fed-deta-content')]/h1/text()")
        loader.add_xpath(
            "cover_image", "//dt[contains(@class, 'fed-deta-images')]/a/@data-original"
        )
        loader.add_value("ref_urls", [response.url])

        for li in response.xpath("//dd[contains(@class, 'fed-deta-content')]/ul/li"):
            label = li.xpath(".//span/text()").get()
            text = li.xpath("./a/text()").get()
            if label == "别名":
                # 17892
                loader.add_value(
                    "aliases",
                    next(filter(lambda str: str != " ", li.xpath("./text()").getall())),
                )
            elif label == "状态":
                loader.add_value("schedule", text)
            elif label == "作者":
                # Wrong author label e.g. https://www.cocomanhua.com/17823/
                loader.add_value(
                    "authors",
                    text[3:] if text.startswith("作者:") else text,
                )
            elif label == "类别":
                loader.add_value("categories", li.xpath("./a/text()").getall())
            elif label == "简介":
                loader.add_value("excerpt", li.xpath("./div/text()").get())

        return loader.load_item()

    def get_catalog(self, response):
        return response.xpath("//div[contains(@class, 'all_data_list')]//li/a")

    def parse_chapter_data(self, response, user_info):
        match = re.findall(r"var C_DATA= ?(.*?);", response.text)

        if len(match) <= 0:
            return

        loaded_chapter = self._load_chapter(demjson.decode(match[0]))

        if not loaded_chapter:
            return

        if not loaded_chapter["page_size"]:
            return

        page_size = int(loaded_chapter["page_size"])

        base_url = (
            "https://"
            + loaded_chapter["domain"]
            + "/comic/"
            + loaded_chapter["img_url_path"]
        )

        start_index = (
            int(loaded_chapter["startimg"]) if loaded_chapter["startimg"] else 0
        )

        loader = MangaChapterLoader()
        loader.add_value("name", loaded_chapter["pagename"])
        loader.add_value("books_query_id", user_info)
        loader.add_value("ref_urls", [response.url])
        loader.add_value(
            "image_urls",
            list(
                map(
                    lambda page: base_url + str(start_index + page).zfill(4) + ".jpg",
                    range(page_size),
                )
            ),
        )

        yield loader.load_item()

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
                OHManhuaSpider._decrypt(dict_value["enc_code1"])
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
