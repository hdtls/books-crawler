import hashlib
import logging
import os
import time

from books_scrapy.items import Manga, MangaChapter
from contextlib import suppress
from itemloaders.utils import arg_to_iter
from itemadapter import ItemAdapter
from io import BytesIO
from PIL import Image
from scrapy.exceptions import DropItem
from scrapy.http.request import Request
from scrapy.pipelines import images
from scrapy.pipelines.files import (
    FSFilesStore,
    FTPFilesStore,
    GCSFilesStore,
    S3FilesStore,
)
from scrapy.utils.log import failure_to_exc_info
from scrapy.utils.python import to_bytes
from scrapy.utils.request import referer_str
from twisted.internet import defer

logger = logging.getLogger(__name__)


class FSImageStore(FSFilesStore):
    def stat_file(self, path, info):
        absolute_path = self._get_filesystem_path(path)
        try:
            last_modified = os.path.getmtime(absolute_path)
        except os.error:
            return {}

        with open(absolute_path, "rb") as f:
            data = f.read()
            checksum = hashlib.md5(data).hexdigest()
            image = Image.open(BytesIO(data))

        return {
            "last_modified": last_modified,
            "checksum": checksum,
            "width": image.width,
            "height": image.height,
        }


class ImagesPipeline(images.ImagesPipeline):
    """Abstract pipeline that implement the image thumbnail generation logic"""

    STORE_SCHEMES = {
        "": FSFilesStore,
        "file": FSImageStore,
        "s3": S3FilesStore,
        "gs": GCSFilesStore,
        "ftp": FTPFilesStore,
    }

    def get_media_requests(self, item, info):
        urls = ItemAdapter(item).get(self.images_urls_field, [])

        if isinstance(item, Manga):
            if item.cover_image:
                urls = item.cover_image.get("url", [])

        yield from [Request(url) for url in arg_to_iter(urls)]

    def media_to_download(self, request, info, *, item=None):
        def _success(result):
            if not result:
                return  # returning None force download

            last_modified = result.get("last_modified", None)
            if not last_modified:
                return  # returning None force download

            age_seconds = time.time() - last_modified
            age_days = age_seconds / 60 / 60 / 24
            if age_days > self.expires:
                return  # returning None force download

            referer = referer_str(request)
            logger.debug(
                "File (uptodate): Downloaded %(medianame)s from %(request)s "
                "referred in <%(referer)s>",
                {"medianame": self.MEDIA_NAME, "request": request, "referer": referer},
                extra={"spider": info.spider},
            )
            self.inc_stats(info.spider, "uptodate")

            checksum = result.get("checksum", None)
            return {
                "url": request.url,
                "path": path,
                "checksum": checksum,
                "width": result["width"],
                "height": result["height"],
                "status": "uptodate",
            }

        path = self.file_path(request, info=info, item=item)
        dfd = defer.maybeDeferred(self.store.stat_file, path, info)
        dfd.addCallbacks(_success, lambda _: None)
        dfd.addErrback(
            lambda f: logger.error(
                self.__class__.__name__ + ".store.stat_file",
                exc_info=failure_to_exc_info(f),
                extra={"spider": info.spider},
            )
        )
        return dfd

    def media_downloaded(self, response, request, info, *, item):
        msg = super().media_downloaded(response, request, info, item=item)
        msg["width"] = msg["checksum"]["width"]
        msg["height"] = msg["checksum"]["height"]
        msg["checksum"] = msg["checksum"]["checksum"]
        return msg

    def file_downloaded(self, response, request, info, *, item):
        checksum = None
        for path, image, buf in self.get_images(response, request, info, item=item):
            if checksum is None:
                buf.seek(0)
                checksum = hashlib.md5(buf.getvalue()).hexdigest()
            width, height = image.size
            self.store.persist_file(
                path,
                buf,
                info,
                meta={"width": width, "height": height},
                headers={"Content-Type": "image/jpeg"},
            )
        return {"checksum": checksum, "width": width, "height": height}

    def item_completed(self, results, item, info):
        with suppress(KeyError):
            print(results, info)
            ItemAdapter(item)[self.images_urls_field] = [
                dict(
                    url=meta["path"],
                    ref_urls=[meta["url"]],
                )
                for success, meta in results
                if success
            ]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        if isinstance(item, Manga):
            return f"{item.make_signature()}/{hashlib.sha1(to_bytes(request.url)).hexdigest()}.jpg"
        elif isinstance(item, MangaChapter):
            filtered = [
                index for index, url in item.image_urls if url["url"] == request.url
            ]
            return f"{item.books_query_id}/{item.make_signature()}/{str(filtered[0]).zfill(4)}.jpg"
        else:
            raise DropItem("Not supported item type.")
