# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
import scrapy.pipelines.images
import hashlib

from books_scrapy.items import MangaChapter
from books_scrapy.items import Image
from books_scrapy.utils import fmt_meta
from books_scrapy.utils import revert_fmt_meta
from books_scrapy.settings import IMAGES_STORE
from itemadapter import ItemAdapter
from pathlib import Path
from PIL import ImageFile
from scrapy import Request
from scrapy.utils.python import to_bytes

ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImagesPipeline(scrapy.pipelines.images.ImagesPipeline):
    def get_media_requests(self, item, info):
        urls = ItemAdapter(item).get(self.images_urls_field, [])

        for url in urls:
            # If url is kind of `Image` class resolve `url` and `file_path`.
            if isinstance(url, Image):
                file_path = url["file_path"]

                # Skip if file already exists.
                if Path(url["file_path"]).exists():
                    continue

                yield scrapy.Request(
                    url["url"],
                    self.on_complete,
                    headers=url["http_headers"],
                    meta=fmt_meta(url),
                )
            else:
                yield Request(url, meta=fmt_meta(url))

    def file_path(self, request, response=None, info=None):
        full_path = revert_fmt_meta(request.meta)["file_path"]

        if full_path:
            full_path = full_path + "/" + revert_fmt_meta(request.meta)["name"]
            return full_path.replace(IMAGES_STORE, "")

        full_path = hashlib.sha1(to_bytes(revert_fmt_meta(request.meta))).hexdigest()
        return f"full/{full_path}.jpg"
