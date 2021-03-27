# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import hashlib

from books_scrapy.utils import list_extend
from dataclasses import dataclass, field
from typing import Any, Optional, List
from sqlalchemy.orm import relationship
from sqlalchemy.orm.decl_api import registry
from sqlalchemy.sql.schema import Column, ForeignKey, Table
from sqlalchemy.sql.sqltypes import (
    ARRAY,
    BigInteger,
    Binary,
    Integer,
    JSON,
    String,
    Text,
)

mapper_registry = registry()


@dataclass
class Image:
    url: str
    name: Optional[str] = None


@dataclass
class Chapter:
    name: str
    book_id: int
    ref_urls: str

    @property
    def fp(self):
        plaintext = self.name.encode("utf-8")
        md5 = hashlib.md5()
        md5.update(plaintext)
        return md5.hexdigest()[8:-8]


@dataclass
@mapper_registry.mapped
class MangaChapter(Chapter):
    __table__ = Table(
        "manga_chapters",
        mapper_registry.metadata,
        Column("id", BigInteger, autoincrement=True, primary_key=True),
        Column("fingerprint", Binary(16), index=True, unique=True),
        Column("image_urls", ARRAY(JSON)),
        Column("book_id", BigInteger, ForeignKey("manga.id")),
    )

    id: int = field(init=False)
    image_urls: List[Image] = field(default_factory=list, default=[])

    @property
    def page_size(self):
        return len(self.image_urls)

    @property
    def fingerprint(self):
        plaintext = self.name.encode("utf-8")
        md5 = hashlib.md5()
        md5.update(plaintext)
        return md5.digest()

    def merge(self, other):
        self.ref_urls = list_extend(self.ref_urls, other.ref_urls)

        if self.page_size < other.page_size:
            self.image_urls = sorted(
                list_extend(self.image_urls, other.image_urls), key=lambda url: url.name
            )


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
        Column("fingerprint", Binary(16), index=True, unique=True),
        Column("name", String(255), nullable=False),
        Column("excerpt", Text, nullable=False),
        Column("ref_urls", ARRAY(String)),
        Column("aliases", ARRAY(String)),
        Column("cover_image", JSON, nullable=False),
        Column("background_image", JSON),
        Column("promo_image", JSON),
        Column("schedule", Integer, nullable=False),
        Column("area_id", ForeignKey("manga_areas.id"), index=True),
    )

    __mapper_args__ = {
        "properties": {
            "chapters": relationship("MangaChapter", backref="manga"),
            # "authors": relationship("User", secondary=author_manga_siblings)
        }
    }

    id: int = field(init=False)
    cover_image: Image
    excerpt: str
    name: str
    area: Optional[str]
    ref_urls: List[str] = field(default_factory=list)
    area_id: Optional[int] = None
    aliases: Optional[List[str]] = None
    background_image: Optional[Image] = None
    promo_image: Optional[Image] = None
    # Schedule for manga publishing. there only have two value,
    # 0 for inprogress or 1 for finished.
    schedule: int = field(default=0)

    authors: List[str] = field(default_factory=list)
    categories: Optional[List[str]] = field(default_factory=list)

    chapters: Optional[List[MangaChapter]] = field(default_factory=list)

    @property
    def fingerprint(self):
        plaintext = self.name + "-" + ",".join(self.authors)
        plaintext = plaintext.encode("utf-8")
        md5 = hashlib.md5()
        md5.update(plaintext)
        return md5.digest()


@dataclass
class MangaChapter(Chapter):
    image_urls: List[Image]

    @property
    def page_size(self):
        return len(self.image_urls)


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
