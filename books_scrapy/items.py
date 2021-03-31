# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import hashlib

from datetime import datetime, timezone
from books_scrapy.utils import list_extend
from dataclasses import dataclass, field
from typing import Optional, List
from sqlalchemy.orm import relationship
from sqlalchemy.orm.decl_api import registry
from sqlalchemy.sql.schema import Column, ForeignKey, Table
from sqlalchemy.sql.sqltypes import (
    BigInteger,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
)

mapper_registry = registry()


@dataclass
class MangaCategory:
    pass


@dataclass
class Image:
    url: str
    name: Optional[str] = None


@dataclass
class Chapter:
    name: str
    ref_urls: Optional[List[str]]
    books_query_id: str = field(repr=False)


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
        Column("created_at", DateTime, default=datetime.now(timezone.utc)),
        Column(
            "updated_at",
            DateTime,
            default=datetime.now(timezone.utc),
            onupdate=datetime.now(timezone.utc),
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


# author_manga_siblings = Table(
#     "author_manga_siblings",
#     mapper_registry.metadata,
#     Column("user_id", Integer, ForeignKey("users.id"), nullable=False, primary_key=True),
#     Column("manga_id", Integer, ForeignKey("manga.id"), nullable=False, primary_key=True),
# )


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
        Column("schedule", Integer, nullable=False),
        Column("ref_urls", JSON(none_as_null=True)),
        Column("aliases", JSON(none_as_null=True)),
        Column("background_image", JSON(none_as_null=True)),
        Column("promo_image", JSON(none_as_null=True)),
        Column("area_id", ForeignKey("manga_areas.id")),
        Column("created_at", DateTime, default=datetime.now(timezone.utc)),
        Column(
            "updated_at",
            DateTime,
            default=datetime.now(timezone.utc),
            onupdate=datetime.now(timezone.utc),
        ),
    )

    __mapper_args__ = {
        "properties": {
            "chapters": relationship("MangaChapter", backref="manga"),
            # "authors": relationship("User", secondary=author_manga_siblings)
        }
    }

    cover_image: dict
    excerpt: str
    name: str
    signature: str
    # Schedule for manga publishing. there only have two value,
    # 0 for inprogress or 1 for finished.
    schedule: int
    authors: List[str] = field(default_factory=list)
    ref_urls: Optional[List[str]] = None
    area: Optional[str] = None
    area_id: Optional[int] = None
    aliases: Optional[List[str]] = None
    background_image: Optional[Image] = None
    promo_image: Optional[Image] = None
    categories: Optional[List[str]] = None
    chapters: Optional[List[MangaChapter]] = field(default_factory=list)

    def make_signature(self):
        plaintext = self.name + "-" + ",".join(self.authors)
        plaintext = plaintext.encode("utf-8")
        md5 = hashlib.md5()
        md5.update(plaintext)
        return md5.hexdigest()

    def merge(self, other):
        """
        Merging two non-copyright manga object properties.
        all properties that describe database relationship will be ignored.
        """

        if not isinstance(other, Manga):
            return

        self.aliases = list_extend(self.aliases, other.aliases)
        self.schedule = other.schedule
        self.ref_urls = list_extend(self.ref_urls, other.ref_urls)
        self.background_image = self.background_image or other.background_image
        self.promo_image = self.background_image or other.background_image


@dataclass
@mapper_registry.mapped
class MangaArea:
    __table__ = Table(
        "manga_areas",
        mapper_registry.metadata,
        Column("id", Integer, autoincrement=True, primary_key=True),
        Column("name", String(), nullable=False, unique=True),
        Column("created_at", DateTime, default=datetime.now(timezone.utc)),
        Column(
            "updated_at",
            DateTime,
            default=datetime.now(timezone.utc),
            onupdate=datetime.now(timezone.utc),
        ),
    )

    __mapper_args__ = {
        "properties": {
            "manga": relationship("Manga", backref="area"),
        },
    }

    name: str
    manga: List[Manga] = field(init=False, default_factory=list)


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
