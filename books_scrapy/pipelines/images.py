import hashlib
import logging
import os

from books_scrapy.utils import fmt_meta
from books_scrapy.utils import revert_fmt_meta
from itemadapter import ItemAdapter
from pathlib import Path
from scrapy.pipelines import images
from scrapy.pipelines.files import (
    FSFilesStore,
    FTPFilesStore,
    GCSFilesStore,
    S3FilesStore,
)
from scrapy.utils.python import to_bytes
from scrapy.utils.project import get_project_settings


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
        # FIXME: DEBUG only, enable download when release.
        return
        for url in urls:
            # If url is kind of `Image` class resolve `url` and `file_path`.
            if isinstance(url, Image):
                file_path = url["file_path"]

                # Skip if file already exists.
                if Path(url["file_path"]).exists():
                    continue

                yield scrapy.Request(
                    url["url"],
                    meta=fmt_meta(url),
                )
            else:
                yield Request(url, meta=fmt_meta(url))

    def file_path(self, request, response=None, info=None, *, item=None):
        full_path = revert_fmt_meta(request.meta)["file_path"]

        if full_path:
            full_path = full_path + "/" + revert_fmt_meta(request.meta)["name"]
            return full_path.replace(get_project_settings["IMAGES_STORE"], "")

        full_path = hashlib.sha1(to_bytes(revert_fmt_meta(request.meta))).hexdigest()
        return f"full/{full_path}.jpg"
