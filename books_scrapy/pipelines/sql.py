import logging

from books_scrapy.items import Manga, MangaChapter
from scrapy.exceptions import DropItem
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine


class MySQLPipeline:
    def __init__(self, crawler):
        """
        Initialize database connection and sessionmaker
        Create tables
        """
        self.settings = crawler.settings
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def open_spider(self, spider):
        engine = create_engine(self.settings["MYSQL_URL"], encoding="utf8")
        self.session: Session = sessionmaker(bind=engine)()

    def close_spider(self, spider):
        self.session.close()

    def process_item(self, item, spider):
        session = self.session

        exsit_item = None

        if isinstance(item, Manga):
            item.signature = item.make_signature()

            exsit_item = (
                session.query(Manga).filter(Manga.signature == item.signature).first()
            )

            if exsit_item:
                exsit_item.merge(item)
            else:
                exsit_item = item
        elif isinstance(item, MangaChapter):
            item.signature = item.make_signature()

            exsit_item = (
                session.query(Manga)
                .filter(Manga.signature == item.books_query_id)
                .first()
            )

            if not exsit_item:
                raise DropItem()

            filtered_item = next(
                filter(lambda el: el.name == item.name, exsit_item.chapters),
                None,
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
                self.logger.error(e)
                self.session.rollback()
        return item