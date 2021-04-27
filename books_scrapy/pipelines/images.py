import hashlib
import logging
import os

from books_scrapy.items import Manga, MangaChapter
from books_scrapy.utils.bili import biligen
from books_scrapy.utils.snowflake import snowflake
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
from scrapy.utils.request import referer_str
from scrapy.utils.project import get_project_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
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

    ref_urls = "ref_urls"

    STORE_SCHEMES = {
        "": FSFilesStore,
        "file": FSImageStore,
        "s3": S3FilesStore,
        "gs": GCSFilesStore,
        "ftp": FTPFilesStore,
    }

    def open_spider(self, spider):
        super().open_spider(spider)
        engine = create_engine(get_project_settings()["MYSQL_URL"], encoding="utf8")
        self.session: Session = sessionmaker(bind=engine)()

    def close_spider(self, spider):
        self.session.close()

    def get_media_requests(self, item, info):
        def _resolve_item_id(session, item):
            if isinstance(item, Manga):
                exsit_item = (
                    session.query(Manga)
                    .filter(Manga.signature == item.signature)
                    .first()
                )
                item.id = exsit_item.id if exsit_item else snowflake()

            elif isinstance(item, MangaChapter):
                exsit_item = (
                    session.query(Manga)
                    .filter(Manga.signature == item.books_query_id)
                    .first()
                )

                if not exsit_item:
                    raise DropItem("Missing parent item.", item)

                filtered_item = next(
                    filter(lambda el: el.name == item.name, exsit_item.chapters),
                    None,
                )

                item.id = filtered_item.id if filtered_item else snowflake()
                item.book_id = exsit_item.id

        _resolve_item_id(self.session, item)

        urls = []

        if isinstance(item, Manga):
            if item.cover_image:
                urls.extend(item.cover_image.get(self.ref_urls, []))
            if item.background_image:
                urls.extend(item.background_image.get(self.ref_urls, []))
            if item.promo_image:
                urls.extend(item.promo_image.get(self.ref_urls, []))
        elif isinstance(item, MangaChapter):
            if item.cover_image:
                urls.extend(item.cover_image.get(self.ref_urls, []))
            for image in item.asset.files:
                urls.extend(image.get(self.ref_urls, []))
        else:
            urls.extend(ItemAdapter(item).get(self.images_urls_field, []))

        return [Request(url) for url in urls]

    def media_to_download(self, request, info, *, item=None):
        def _success(result):
            import time

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

    def media_downloaded(self, response, request, info, *, item=None):
        msg = super().media_downloaded(response, request, info, item=item)
        msg["width"] = msg["checksum"]["width"]
        msg["height"] = msg["checksum"]["height"]
        msg["checksum"] = msg["checksum"]["checksum"]
        return msg

    def file_downloaded(self, response, request, info, *, item=None):
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
        for result in results:
            if not result[0]:
                logger.debug(result[1])
                continue

            urls = [result[1]["url"]]

            if isinstance(item, Manga):
                # If item is Manga instance there are several field needs update.
                # e.g. cover_image, background_image, promo_image.
                if item.cover_image and urls == item.cover_image.get(self.ref_urls):
                    item.cover_image = self._make_asset_file(result)
                elif item.background_image and urls == item.background_image.get(
                    self.ref_urls
                ):
                    item.background_image = self._make_asset_file(result)
                elif item.promo_image and urls == item.promo_image.get(self.ref_urls):
                    item.promo_image = self._make_asset_file(result)
            elif isinstance(item, MangaChapter):
                files = item.asset.files
                if item.cover_image and urls == item.cover_image.get(self.ref_urls):
                    item.cover_image = self._make_asset_file(result)
                else:
                    for index, image in enumerate(item.asset.files):
                        if urls == image.get(self.ref_urls):
                            # Keep index same as original.
                            files[index] = self._make_asset_file(result)
                item.asset.files = files

            else:
                ItemAdapter(item)[self.images_urls_field] = [
                    meta["path"] for success, meta in results if success
                ]

        if isinstance(item, MangaChapter):
            # Filter success downloaded image files.
            item.asset.files = list(
                filter(lambda file: file.get("url"), item.asset.files)
            )
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        """Override file_path with id relative value to reduce duplicated downloads from difference spider."""
        if isinstance(item, Manga):
            if item.cover_image and item.cover_image.get(self.ref_urls, []) == [
                request.url
            ]:
                return self._resolve_file_path(item.id, "cover_image")
            elif item.background_image and item.background_image.get(
                self.ref_urls, []
            ) == [request.url]:
                return self._resolve_file_path(item.id, "background_image")
            elif item.promo_image and item.promo_image.get(self.ref_urls, []) == [
                request.url
            ]:
                return self._resolve_file_path(item.id, "promo_image")
        elif isinstance(item, MangaChapter):
            if item.cover_image and item.cover_image.get(self.ref_urls, []) == [
                request.url
            ]:
                return self._resolve_file_path([item.book_id, item.id], "cover_image")
            else:
                for index, file in enumerate(item.asset.files):
                    if file.get(self.ref_urls, []) == [request.url]:
                        return self._resolve_file_path(
                            [item.book_id, item.id], f"{index}"
                        )
        else:
            return super().file_path(request, response=response, info=info, item=item)

    def _resolve_file_path(self, args, filename):
        from scrapy.utils.misc import arg_to_iter
        from scrapy.utils.python import to_bytes

        return f"full/{'/'.join(map(lambda arg: biligen(arg), arg_to_iter(args)))}/{hashlib.sha1(to_bytes(filename)).hexdigest()}.jpg"

    def _make_asset_file(self, result):
        failure = result[0]
        if not failure:
            return None

        meta = result[1]
        return dict(
            url=meta["path"],
            ref_urls=[meta["url"]],
            width=meta["width"],
            height=meta["height"],
        )
