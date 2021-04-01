import logging

from books_scrapy.items import Author, Manga, MangaArea, MangaChapter
from books_scrapy.utils import list_diff
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

            # Make relationship between manga and areas.
            # This operation is only triggered when `item.area` not None and `exsit_item` 
            # is None or `exsit_item` not None  and`exsit_item.area_id` is None.
            if item.area and (
                not exsit_item or (exsit_item and not exsit_item.area_id)
            ):
                # Try to query `MangaArea.id` from db. If exsit write it to `item` else
                # save `item.area` as new `MangaArea` item. then asign id value to `item`.
                area_id = (
                    session.query(MangaArea.id)
                    .filter(MangaArea.name == item.area)
                    .first()
                )
                if area_id:
                    item.area_id = area_id
                else:
                    item.area_id = self._handle_write(item.area).id

            orig_authors = []
            if exsit_item:
                orig_authors = exsit_item.authors
            else:
                # Query all authors that name in item.authors
                orig_authors = (
                    session.query(Author)
                    .filter(Author.name.in_(map(lambda e: e.name, item.authors)))
                    .all()
                )

            # Register zombie user for new author that not exsit in saved `manga.authors`
            # and update `manga.authors` to new value.
            # For some reasons, we only do incremental updates for book author relationship.
            for i in list_diff(orig_authors, item.authors).added:
                written = self._handle_write(i)
                orig_authors.append(written)
                item.authors = orig_authors

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