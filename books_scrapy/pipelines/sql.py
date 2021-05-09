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
            exist_item = self.get_persisted_manga(session, item)

            if exist_item and exist_item.copyrighted:
                raise DropItem("Ignore copyrighted item.", item)

            # Link manga and area.
            # This operation is only triggered when `item.area` is not None and `exsit_item`
            # is None or `exsit_item` not None but `exsit_item.area_id` is None.
            if item.area and (
                not exist_item or (exist_item and not exist_item.area_id)
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
                    session.add(item.area)
                    item.area_id = self.handle_write(session, item.area).id

            # Make relationship between manga and authors.
            orig_authors = []
            if exist_item:
                orig_authors = exist_item.authors
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
                session.add(i)
                written = self.handle_write(session, i)
                orig_authors.append(written)
                item.authors = orig_authors

            # Link manga and categories.
            orig_CAT = None
            if exist_item:
                orig_CAT = exist_item.categories
            else:
                orig_CAT = (
                    session.query(m.MangaCategory)
                    .filter(
                        m.MangaCategory.name.in_(map(lambda e: e.name, item.categories))
                    )
                    .all()
                )

            for i in iter_diff(orig_CAT, item.categories).added:
                session.add(i)
                written = self.handle_write(session, i)
                orig_CAT.append(written)
                item.categories = orig_CAT

            if exist_item:
                exist_item.merge(item)
                return self.handle_write(session, exist_item)
            else:
                exist_item = item
                session.add(exist_item)
                return self.handle_write(session, exist_item)

        elif isinstance(item, m.MangaChapter):
            exist_item = self.get_persisted_manga(session, item.manga)

            if not exist_item:
                raise DropItem("Missing parent item.", item)

            filtered_item = next(
                filter(lambda el: el.name == item.name, exist_item.chapters),
                None,
            )

            if filtered_item:
                filtered_item.merge(item)
                return self.handle_write(session, filtered_item)
            else:
                item.book_id = exist_item.id
                exist_item.chapters.append(item)
                return self.handle_write(session, item)

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
            # .join(m.MangaCategory, m.Manga.categories)
            # .join(m.MangaChapter, m.Manga.chapters)
            # .join(m.MangaArea, m.Manga.area)
            .first()
        )

    @staticmethod
    def handle_write(session, item):
        """
        Flush changes and add new item to db if is_add is true.
        """

        try:
            session.commit()
            return item
        except SQLAlchemyError as e:
            logger.error(e)
            session.rollback()