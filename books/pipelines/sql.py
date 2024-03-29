import logging

import books.items as m
from books.utils.diff import iter_diff
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
from sqlalchemy import create_engine, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, scoped_session

logger = logging.getLogger(__name__)
logger.setLevel = get_project_settings()["LOG_LEVEL"]

engine = create_engine(get_project_settings()["MYSQL_URL"], encoding="utf8", echo=False)
session_factory = scoped_session(sessionmaker(bind=engine))

class MySQLPipeline:

    def open_spider(self, spider):
        self.session = session_factory()

    def close_spider(self, spider):
        self.session.close()

    def process_item(self, item, spider):
        session = self.session

        if isinstance(item, m.Manga):

            exist_item = self._get_specified_manga(session, item)

            if exist_item and exist_item.copyrighted:
                raise DropItem("Ignore copyrighted item.", item)

            # Link manga and area.
            # This operation is only triggered when `item.area` is not None and `exsit_item`
            # is None or `exsit_item` not None but `exsit_item.area_id` is None.
            if item.area and (not exist_item or (exist_item and not exist_item.area)):
                # Try to query `MangaArea.id` from db. If exsit write it to `item` else
                # save `item.area` as new `MangaArea` item. then asign id value to `item`.
                filtered_area = (
                    session.query(m.MangaArea)
                    .filter(m.MangaArea.name == item.area.name)
                    .first()
                )
                if filtered_area:
                    item.area = filtered_area

            # Make relationship between manga and authors.
            orig_authors = []
            if exist_item:
                orig_authors = exist_item.authors
            else:
                # Query all authors that name in item.authors
                orig_authors = (
                    session.query(m.Author)
                    .filter(
                        m.Author.username.in_(map(lambda e: e.username, item.authors))
                    )
                    .all()
                )

            # Register zombie user for new author that not exsit in saved `manga.authors`
            # and update `manga.authors` to new value.
            # For some reasons, we only do incremental updates for book author relationship.
            for i in iter_diff(orig_authors, item.authors).added:
                orig_authors.append(i)
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
                # session.add(i)
                # self.handle_write(session, i)
                # written = i
                orig_CAT.append(i)
            item.categories = orig_CAT

            if exist_item:
                exist_item.merge(item)
            else:
                exist_item = item
                session.add(exist_item)

            self.handle_write(session)
            return exist_item

        elif isinstance(item, m.MangaChapter):
            exist_item = self._get_specified_manga(session, item.manga)

            if not exist_item:
                raise DropItem("Missing parent item.", item)

            filtered_item = next(
                filter(lambda el: el.name == item.name, exist_item.chapters),
                None,
            )

            if filtered_item:
                filtered_item.merge(item)
                self.handle_write(session)
                return filtered_item
            else:
                exist_item.chapters.append(item)
                self.handle_write(session)
                return item

    def _get_specified_manga(self, session, manga):
        return (
            session.query(m.Manga)
            .filter(
                or_(
                    m.Manga.name == manga.name,
                    m.Manga.aliases.contains((manga.aliases or []) + [manga.name]),
                )
            )
            .join(m.Manga.authors)
            .filter(
                m.Author.username.in_(list(map(lambda author: author.username, manga.authors)))
            )
            .first()
        )

    @staticmethod
    def handle_write(session):
        """
        Flush changes and add new item to db if is_add is true.
        """

        try:
            session.flush()
            session.commit()
        except SQLAlchemyError as e:
            logger.error(e)
            session.rollback()
