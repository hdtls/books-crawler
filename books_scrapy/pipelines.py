import scrapy
import hashlib

from sqlalchemy.exc import SQLAlchemyError
from books_scrapy.items import Manga, MangaChapter
from books_scrapy.items import Image
from books_scrapy.utils import fmt_meta
from books_scrapy.utils import revert_fmt_meta
from books_scrapy.settings import IMAGES_STORE
from itemadapter import ItemAdapter
from pathlib import Path
from scrapy import Request
from scrapy.pipelines import images
from scrapy.utils.python import to_bytes
from scrapy.exceptions import DropItem


class ImagesPipeline(images.ImagesPipeline):
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
            return full_path.replace(IMAGES_STORE, "")

        full_path = hashlib.sha1(to_bytes(revert_fmt_meta(request.meta))).hexdigest()
        return f"full/{full_path}.jpg"


from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine


class MySQLPipeline(object):  #
    """
    Defaults:
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = None
    MYSQL_PASSWORD = ''
    MYSQL_DB = None
    MYSQL_TABLE = None
    MYSQL_UPSERT = False
    MYSQL_RETRIES = 3
    MYSQL_CLOSE_ON_ERROR = True
    MYSQL_CHARSET = 'utf8'
    Pipeline:
    ITEM_PIPELINES = {
       'scrapy_mysql_pipeline.MySQLPipeline': 300,
    }
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        """
        Initialize database connection and sessionmaker
        Create tables
        """

        self.settings = crawler.settings

        engine = create_engine(self.settings["MYSQL_URL"])
        self.session: Session = sessionmaker(bind=engine)()

    def close_spider(self, spider):
        self.session.close()

    def process_item(self, item, spider):
        session = self.session

        exsit_item = None

        if isinstance(item, Manga):
            item.fingerprint = item.make_fingerprint()

            exsit_item: Manga = (
                session.query(Manga)
                .filter(Manga.fingerprint == item.fingerprint)
                .first()
            )

            if exsit_item:
                exsit_item.merge(item)
            else:
                exsit_item = item
        elif isinstance(item, MangaChapter):
            item.fingerprint = item.make_fingerprint()

            exsit_item: Manga = (
                session.query(Manga)
                .filter(Manga.fingerprint == item.book_unique)
                .join(Manga.chapters)
                .first()
            )

            if not exsit_item:
                raise DropItem()

            filtered_item: MangaChapter = next(
                filter(lambda el: el.name == item.name, exsit_item.chapters)
            )

            if filtered_item:
                filtered_item.merge(item)
            else:
                item.book_id = exsit_item.id
                exsit_item.chapters.append(item)

        if exsit_item:
            try:
                session.add(exsit_item)
                session.commit()
            except SQLAlchemyError as e:
                spider.logger.error(e)
                session.rollback()

        return exsit_item
