import logging

import books_scrapy.items as m
from books_scrapy.utils.diff import iter_diff
from scrapy.exceptions import DropItem
from sqlalchemy import create_engine, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


class MySQLPipeline:
    def __init__(self, crawler):
        self.settings = crawler.settings

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

        if isinstance(item, m.Manga):
            exsit_item = self.get_persisted_manga(session, item)

            if exsit_item and exsit_item.copyrighted:
                raise DropItem("Ignore copyrighted item.", item)

            # Link manga and area.
            # This operation is only triggered when `item.area` is not None and `exsit_item`
            # is None or `exsit_item` not None but `exsit_item.area_id` is None.
            if item.area and (
                not exsit_item or (exsit_item and not exsit_item.area_id)
            ):
                # Try to query `MangaArea.id` from db. If exsit write it to `item` else
                # save `item.area` as new `MangaArea` item. then asign id value to `item`.
                area_id = (
                    session.query(m.MangaArea.id)
                    .filter(m.MangaArea.name == item.area.name)
                    .first()
                )
                if area_id:
                    item.area_id = area_id
                else:
                    item.area_id = self.handle_write(session, item.area).id

            # Make relationship between manga and authors.
            orig_authors = []
            if exsit_item:
                orig_authors = exsit_item.authors
            else:
                # Query all authors that name in item.authors
                orig_authors = (
                    session.query(m.Author)
                    .filter(m.Author.name.in_(map(lambda e: e.name, item.authors)))
                    .all()
                )

            # Register zombie user for new author that not exsit in saved `manga.authors`
            # and update `manga.authors` to new value.
            # For some reasons, we only do incremental updates for book author relationship.
            for i in iter_diff(orig_authors, item.authors).added:
                written = self.handle_write(session, i)
                orig_authors.append(written)
                item.authors = orig_authors

            # Link manga and categories.
            orig_CAT = None
            if exsit_item:
                orig_CAT = exsit_item.categories
            else:
                orig_CAT = (
                    session.query(m.MangaCategory)
                    .filter(
                        m.MangaCategory.name.in_(map(lambda e: e.name, item.categories))
                    )
                    .all()
                )

            for i in iter_diff(orig_CAT, item.categories).added:
                written = self.handle_write(session, i)
                orig_CAT.append(written)
                item.categories = orig_CAT

            if exsit_item:
                exsit_item.merge(item)
                return self.handle_write(session, exsit_item)
            else:
                exsit_item = item
                return self.handle_write(session, exsit_item, True)

        elif isinstance(item, m.MangaChapter):
            is_add = False

            exsit_item = self.get_persisted_manga(session, item.manga)

            if not exsit_item:
                raise DropItem("Missing parent item.", item)

            filtered_item = next(
                filter(lambda el: el.name == item.name, exsit_item.chapters),
                None,
            )

            if filtered_item:
                filtered_item.merge(item)
                self.handle_write(session, exsit_item, is_add=is_add)
                return filtered_item
            else:
                item.book_id = exsit_item.id
                exsit_item.chapters.append(item)
                self.handle_write(session, exsit_item, is_add=is_add)
                return item

    @staticmethod
    def get_persisted_manga(session, item):
        return (
            session.query(m.Manga)
            .filter(
                or_(
                    m.Manga.name == item.name,
                    m.Manga.aliases.contains((item.aliases or []) + [item.name]),
                )
            )
            .join(m.Author, m.Manga.authors)
            .filter(m.Author.name.in_(map(lambda a: a.name, item.authors)))
            .first()
        )

    @staticmethod
    def handle_write(session, item, is_add=False):
        """
        Flush changes and add new item to db if is_add is true.
        """
        if item and is_add:
            session.add(item)

        try:
            session.commit()
        except SQLAlchemyError as e:
            logger.error(e)
            session.rollback()

        return item
