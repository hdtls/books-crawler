import base64
import json
import re

from books.items import *
from books.loaders import ChapterLoader, MangaLoader
from books.utils.misc import formatted_meta, revert_formatted_meta
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from scrapy_redis.spiders import RedisSpider


class CocoMangaSpider(RedisSpider):
    name = "coco"

    def parse(self, response, **kwargs):
        book_info = self.parse_details(response)
        catalog = self.parse_catalog(response)
        if not catalog:
            return

        if not book_info:
            return

        yield book_info

        meta = formatted_meta(book_info)
        meta["playwright"] = True

        yield from response.follow_all(catalog[:1], callback=self.parse_chapter_data, meta=meta)

    def parse_details(self, response):
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
                loader.add_value("aliases", li.xpath("./text()").get())
            elif label == "状态":
                loader.add_value("schedule", text)
            elif label == "作者":
                # Wrong author label e.g. https://www.cocomanhua.com/17823/
                loader.add_value("authors", text)
            elif label == "类别":
                loader.add_value("categories", li.xpath("./a/text()").getall())
            elif label == "简介":
                loader.add_value("excerpt", li.xpath("./div/text()").get())

        return loader.load_item()

    def parse_catalog(self, response):
        return list(
            reversed(
                response.xpath(
                    "//div[contains(@class, 'all_data_list')]//li/a/@href"
                ).getall()
            )
        )

    def parse_chapter_data(self, response):
        match = re.findall(r"var C_DATA= ?(.*?);", response.text)

        if len(match) <= 0:
            return

        loaded_chapter = None
        loaded_chapter = self._load_chapter(match[0].strip('\''))

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

        loader = ChapterLoader()
        loader.add_value("name", loaded_chapter["pagename"])
        loader.add_value("ref_urls", [response.url])
        loader.add_value(
            "assets",
            list(
                map(
                    lambda page: base_url + str(start_index + page).zfill(4) + ".jpg",
                    range(page_size),
                )
            ),
        )

        item = loader.load_item()
        item.manga = revert_formatted_meta(response.meta)
        yield item

    @staticmethod
    def _load_chapter(ciphertext):
        assert isinstance(ciphertext, str)

        plaintext = CocoMangaSpider._decrypt(ciphertext)

        match = re.findall(r"mh_info=(.*?);", plaintext)

        if not match:
            return None

        # If matched then serializing first match to original chapter dict value.
        dict_value = json.loads(match[0].strip('\''))
        dict_value = None

        if dict_value["enc_code1"]:
            dict_value["page_size"] = int(
                CocoMangaSpider._decrypt(dict_value["enc_code1"])
            )

        if dict_value["enc_code2"]:
            dict_value["img_url_path"] = CocoMangaSpider._decrypt(
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
            try:
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
            except:
                pass

        return ciphertext.decode()
