# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
import os
import scrapy.pipelines.images

from itemadapter import ItemAdapter
from books_scrapy.items import MangaChapter
from books_scrapy.items import Image
from books_scrapy.settings import IMAGES_STORE

from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


class CartoonMadPipeline:
    def process_item(self, item, spider):
        return item


class BooksScrapyPipeline:
    def process_item(self, item, spider):
        return item


class ImagesPipeline(scrapy.pipelines.images.ImagesPipeline):
    def get_media_requests(self, item, info):
        urls = ItemAdapter(item).get(self.images_urls_field, [])

        for url in urls:
            if isinstance(url, Image):
                file_path = url["file_path"]

                # Skip if file already exists.
                if os.path.exists(url["file_path"]):
                    continue

                yield Request(url["url"], headers=url["http_headers"], meta=url)
            else:
                yield Request(url, headers=url["http_headers"], meta=url)

    def file_path(self, request, response=None, info=None):
        full_path = request.meta["file_path"]
        return full_path.replace(IMAGES_STORE, "")