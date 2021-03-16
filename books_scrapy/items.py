# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

from dataclasses import dataclass
from typing import Optional


@dataclass
class Image:
    url: str
    name: Optional[str] = None
    file_path: Optional[str] = None
    http_headers: Optional[dict] = None


@dataclass
class Manga:
    # define the fields for your item here like:
    authors: list[str]
    cover_image: Image
    excerpt: str
    name: str
    ref_url: str
    area: Optional[str] = None
    alias: Optional[str] = None
    background_image: Optional[Image] = None
    promo_image: Optional[Image] = None
    status: Optional[str] = None
    categories: Optional[list[str]] = None


@dataclass
class MangaChapter:
    name: str
    ref_url: str
    rel_m_id: str
    rel_m_title: str
    image_urls: list[Image]

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
