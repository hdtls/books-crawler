# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import enum
import hashlib

from datetime import datetime

from books_scrapy.utils import iter_diff, list_extend
from dataclasses import dataclass, field
from typing import Optional, List
from sqlalchemy.orm import relationship
from sqlalchemy.orm.decl_api import registry
from sqlalchemy.sql.schema import Column, ForeignKey, Table
from sqlalchemy.sql.sqltypes import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Integer,
    JSON,
    String,
    Text,
)


mapper_registry = registry()


class Level(enum.Enum):
    zombie = "zombie"


@dataclass
@mapper_registry.mapped
class Author:
    __table__ = Table(
        "users",
        mapper_registry.metadata,
        Column("id", BigInteger, autoincrement=True, nullable=False, primary_key=True),
        Column("name", String, nullable=False, unique=True),
        Column("level", Enum(Level), default=Level.zombie, nullable=False),
        Column("created_at", DateTime, default=datetime.utcnow()),
        Column(
            "updated_at",
            DateTime,
            default=datetime.utcnow(),
            onupdate=datetime.utcnow(),
        ),
    )

    name: str

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Author):
            return False
        return self.name == o.name


@dataclass
@mapper_registry.mapped
class MangaCategory:
    __table__ = Table(
        "manga_categories",
        mapper_registry.metadata,
        Column("id", BigInteger, autoincrement=True, nullable=False, primary_key=True),
        Column("name", String, nullable=False, unique=True),
        Column("created_at", DateTime, default=datetime.utcnow()),
        Column(
            "updated_at",
            DateTime,
            default=datetime.utcnow(),
            onupdate=datetime.utcnow(),
        ),
    )

    name: str

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, MangaCategory):
            return False
        return self.name == o.name


@dataclass
class Chapter:
    name: str
    ref_urls: Optional[List[str]]
    books_query_id: str = field(repr=False)


@dataclass
@mapper_registry.mapped
class MangaArea:
    __table__ = Table(
        "manga_areas",
        mapper_registry.metadata,
        Column("id", Integer, autoincrement=True, primary_key=True),
        Column("name", String(), nullable=False, unique=True),
        Column("created_at", DateTime, default=datetime.utcnow()),
        Column(
            "updated_at",
            DateTime,
            default=datetime.utcnow(),
            onupdate=datetime.utcnow(),
        ),
    )

    __mapper_args__ = {
        "properties": {
            "manga": relationship("Manga"),
        },
    }

    name: str

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, MangaArea):
            return False
        return self.name == o.name


@dataclass
@mapper_registry.mapped
class MangaChapter(Chapter):
    __table__ = Table(
        "manga_chapters",
        mapper_registry.metadata,
        Column("id", BigInteger, autoincrement=True, primary_key=True),
        Column("signature", String(32), nullable=False, unique=True),
        Column("name", String, nullable=False),
        Column("image_urls", JSON(none_as_null=True), nullable=False),
        Column("ref_urls", JSON(none_as_null=True)),
        Column("book_id", BigInteger, ForeignKey("manga.id")),
        Column("created_at", DateTime, default=datetime.utcnow()),
        Column(
            "updated_at",
            DateTime,
            default=datetime.utcnow(),
            onupdate=datetime.utcnow(),
        ),
    )

    signature: str
    image_urls: List[dict]

    @property
    def page_size(self):
        return len(self.image_urls)

    def make_signature(self):
        plaintext = self.books_query_id + self.name
        plaintext = plaintext.encode("utf-8")
        md5 = hashlib.md5()
        md5.update(plaintext)
        return md5.hexdigest()

    def merge(self, other):
        self.ref_urls = list_extend(self.ref_urls, other.ref_urls)

        if self.page_size < other.page_size:
            self.image_urls = other.image_urls


author_published_manga = Table(
    "users_manga_linkers",
    mapper_registry.metadata,
    Column("id", BigInteger, autoincrement=True, nullable=False, primary_key=True),
    Column("from", BigInteger, ForeignKey("users.id")),
    Column("to", BigInteger, ForeignKey("manga.id")),
)

categorized_manga = Table(
    "manga_categories_manga_linkers",
    mapper_registry.metadata,
    Column("id", BigInteger, autoincrement=True, nullable=False, primary_key=True),
    Column("from", BigInteger, ForeignKey("manga_categories.id")),
    Column("to", BigInteger, ForeignKey("manga.id")),
)


@dataclass
@mapper_registry.mapped
class Manga:
    __table__ = Table(
        "manga",
        mapper_registry.metadata,
        Column("id", BigInteger, autoincrement=True, primary_key=True),
        Column("signature", String(32), nullable=True, unique=True),
        Column("name", String(255), nullable=False),
        Column("excerpt", Text, nullable=False),
        Column("cover_image", JSON(none_as_null=True), nullable=False),
        Column("copyrighted", Boolean, default=False, nullable=False),
        Column("schedule", Integer, nullable=False),
        Column("ref_urls", JSON(none_as_null=True)),
        Column("aliases", JSON(none_as_null=True)),
        Column("background_image", JSON(none_as_null=True)),
        Column("promo_image", JSON(none_as_null=True)),
        Column("area_id", ForeignKey("manga_areas.id")),
        Column("created_at", DateTime, default=datetime.utcnow()),
        Column(
            "updated_at",
            DateTime,
            default=datetime.utcnow(),
            onupdate=datetime.utcnow(),
        ),
    )

    __mapper_args__ = {
        "properties": {
            "chapters": relationship("MangaChapter", backref="manga"),
            "authors": relationship(
                "Author", secondary=author_published_manga, backref="manga"
            ),
            "categories": relationship(
                "MangaCategory", secondary=categorized_manga, backref="manga"
            ),
        }
    }

    cover_image: dict
    excerpt: str
    name: str
    signature: str
    # Schedule for manga publishing. there only have two value,
    # 0 for inprogress or 1 for finished.
    schedule: int
    # Relationship property remove from init.
    authors: List[Author] = field(init=False)
    copyrighted: bool = field(default=False, init=False)
    ref_urls: Optional[List[str]] = None
    # Use for update `area_id` this is not db column.
    area: Optional[MangaArea] = None
    # area_id: Optional[int] = field(default=None, init=False, repr=False)
    aliases: Optional[List[str]] = None
    background_image: Optional[dict] = None
    promo_image: Optional[dict] = None
    categories: Optional[List[MangaCategory]] = None
    # Children relationshp
    chapters: Optional[List[MangaChapter]] = None

    def make_signature(self):
        plaintext = (
            self.name + "-" + ",".join(map(lambda author: author.name, self.authors))
        )
        plaintext = plaintext.encode("utf-8")
        md5 = hashlib.md5()
        md5.update(plaintext)
        return md5.hexdigest()

    def merge(self, other):
        """
        Incremental merge two non-copyright manga object properties.
        all properties that describe database relationship will be ignored.
        """
        if not isinstance(other, Manga) or self.copyrighted:
            return

        if other.area_id:
            self.area_id = other.area_id

        self.aliases = list_extend(self.aliases, other.aliases)
        self.schedule = other.schedule
        self.ref_urls = list_extend(self.ref_urls, other.ref_urls)
        self.background_image = self.background_image or other.background_image
        self.promo_image = self.background_image or other.background_image

        for author in iter_diff(self.authors, other.authors).added:
            self.authors.append(author)

        for category in iter_diff(self.categories, other.categories).added:
            self.categories.append(category)


@dataclass
class QTcmsObject:
    qTcms_Cur: Optional[str]
    qTcms_S_m_id: Optional[str]
    qTcms_S_p_id: Optional[str]
    qTcms_S_m_name: Optional[str]
    qTcms_S_classid1pinyin: Optional[str]
    qTcms_S_titlepinyin: Optional[str]
    qTcms_S_m_playm: Optional[str]
    qTcms_S_m_mhttpurl: Optional[str]
    qTcms_S_m_murl_e: Optional[str]
    qTcms_S_m_murl_e2: Optional[str]
    qTcms_S_m_murl_e3: Optional[str]
    qTcms_Pic_nextArr: Optional[str]
    qTcms_Pic_backArr: Optional[str]
    qTcms_Pic_curUrl: Optional[str]
    qTcms_Pic_nextUrl: Optional[str]
    qTcms_Pic_nextUrl_Href: Optional[str]
    qTcms_Pic_len: Optional[str]
    qTcms_Pic_backUrl: Optional[str]
    qTcms_Pic_backUrl_Href: Optional[str]
    qTcms_Pic_Cur_m_id: Optional[str]
    qTcms_Pic_m_if: Optional[str]
    qTcms_Pic_m_status2: Optional[str]
    qTcms_m_moban: Optional[str]
    qTcms_m_indexurl: Optional[str]
    qTcms_m_webname: Optional[str]
    qTcms_m_weburl: Optional[str]
    qTcms_m_playurl: Optional[str]
    qTcms_m_url: Optional[str]
    qTcms_S_show_1: Optional[str]
    qTcms_S_ifpubu: Optional[str]
