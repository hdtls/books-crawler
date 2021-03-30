import logging

from books_scrapy.items import Manga, MangaChapter
from scrapy.exceptions import DropItem
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine


logger = logging.getLogger(__name__)


class MySQLPipeline:
    def __init__(self, crawler):
        """
        Initialize database connection and sessionmaker
        Create tables
        """
        self.settings = crawler.settings

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def open_spider(self, spider):
        engine = create_engine(self.settings["MYSQL_URL"])
        self.session: Session = sessionmaker(bind=engine)()

    def close_spider(self, spider):
        self.session.close()

    def process_item(self, item: Manga, spider):
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

        return self._handle_write(exsit_item)

    def _handle_write(self, item):
        if item:
            try:
                self.session.add(item)
                self.session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                self.session.rollback()
        return item