import scrapy
import hashlib


from books_scrapy.items import Manga, MangaChapter
from books_scrapy.items import Image
from books_scrapy.utils import fmt_meta, list_extend
from books_scrapy.utils import revert_fmt_meta
from books_scrapy.settings import IMAGES_STORE
from itemadapter import ItemAdapter
from pathlib import Path
from scrapy import Request
from scrapy.utils.python import to_bytes


class ImagesPipeline(scrapy.pipelines.images.ImagesPipeline):
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

        if isinstance(item, Manga):
            exsit_item: Manga = (
                session.query(Manga)
                .filter(Manga.fingerprint == item.fingerprint)
                .join(Manga.chapters)
                .first()
            )

            if exsit_item:
                exsit_item.aliases = list_extend(exsit_item.aliases, item.aliases)
                exsit_item.area = item.area or exsit_item.area

                if item.chapters:
                    chapter = item.chapters[0]
                    filtered_item: MangaChapter = next(
                        filter(
                            lambda c: c.fingerprint == chapter.fingerprint,
                            exsit_item.chapters,
                        ),
                        None,
                    )
                    if filtered_item:
                        filtered_item.ref_urls = list_extend(
                            filtered_item.ref_urls, chapter.ref_urls
                        )

                        if filtered_item.page_size < chapter.page_size:
                            image_urls = chapter.image_urls
                            filtered_item.image_urls = [
                                filtered_item.image_urls.append(url)
                                for url in image_urls
                                if not url in filtered_item.image_urls
                            ]
                    else:
                        exsit_item.chapters.append(chapter)
            else:
                exsit_item = item
            try:
                session.add(exsit_item)
                session.commit()
            except:
                session.rollback()

        return item
