import base64
import datetime
import json
import re
import scrapy

from books_scrapy.items import *
from books_scrapy.utils import *
from scrapy import Request

class QTcmsObject:
    def __init__(
        self,
        qTcms_Cur,
        qTcms_S_m_id,
        qTcms_S_p_id,
        qTcms_S_m_name,
        qTcms_S_classid1pinyin,
        qTcms_S_titlepinyin,
        qTcms_S_m_playm,
        qTcms_S_m_mhttpurl,
        qTcms_S_m_murl_e,
        qTcms_S_m_murl_e2,
        qTcms_S_m_murl_e3,
        qTcms_Pic_nextArr,
        qTcms_Pic_backArr,
        qTcms_Pic_curUrl,
        qTcms_Pic_nextUrl,
        qTcms_Pic_nextUrl_Href,
        qTcms_Pic_len,
        qTcms_Pic_backUrl,
        qTcms_Pic_backUrl_Href,
        qTcms_Pic_Cur_m_id,
        qTcms_Pic_m_if,
        qTcms_Pic_m_status2,
        qTcms_m_moban,
        qTcms_m_indexurl,
        qTcms_m_webname,
        qTcms_m_weburl,
        qTcms_m_playurl,
        qTcms_m_url,
        qTcms_S_show_1,
        qTcms_S_ifpubu,
    ):
        self.qTcms_Cur = qTcms_Cur
        self.qTcms_S_m_id = qTcms_S_m_id
        self.qTcms_S_p_id = qTcms_S_p_id
        self.qTcms_S_m_name = qTcms_S_m_name
        self.qTcms_S_classid1pinyin = qTcms_S_classid1pinyin
        self.qTcms_S_titlepinyin = qTcms_S_titlepinyin
        self.qTcms_S_m_playm = qTcms_S_m_playm
        self.qTcms_S_m_mhttpurl = qTcms_S_m_mhttpurl
        self.qTcms_S_m_murl_e = qTcms_S_m_murl_e
        self.qTcms_S_m_murl_e2 = qTcms_S_m_murl_e2
        self.qTcms_S_m_murl_e3 = qTcms_S_m_murl_e3
        self.qTcms_Pic_nextArr = qTcms_Pic_nextArr
        self.qTcms_Pic_backArr = qTcms_Pic_backArr
        self.qTcms_Pic_curUrl = qTcms_Pic_curUrl
        self.qTcms_Pic_nextUrl = qTcms_Pic_nextUrl
        self.qTcms_Pic_nextUrl_Href = qTcms_Pic_nextUrl_Href
        self.qTcms_Pic_len = qTcms_Pic_len
        self.qTcms_Pic_backUrl = qTcms_Pic_backUrl
        self.qTcms_Pic_backUrl_Href = qTcms_Pic_backUrl_Href
        self.qTcms_Pic_Cur_m_id = qTcms_Pic_Cur_m_id
        self.qTcms_Pic_m_if = qTcms_Pic_m_if
        self.qTcms_Pic_m_status2 = qTcms_Pic_m_status2
        self.qTcms_m_moban = qTcms_m_moban
        self.qTcms_m_indexurl = qTcms_m_indexurl
        self.qTcms_m_webname = qTcms_m_webname
        self.qTcms_m_weburl = qTcms_m_weburl
        self.qTcms_m_playurl = qTcms_m_playurl
        self.qTcms_m_url = qTcms_m_url
        self.qTcms_S_show_1 = qTcms_S_show_1
        self.qTcms_S_ifpubu = qTcms_S_ifpubu

class The517MangaSpider(scrapy.Spider):
    name = "qtcms"
    img_base_url = None
    qTcms_m_indexurl = "http://images.yiguahai.com"

    start_urls = [
        # "https://www.733.so/mh/32930/702551.html"
        "http://www.517manhua.com/maoxian/weihewurenjidewodeshijie/1174169.html"
    ]

    def parse(self, response):
        return self.parse_chapter_data(response)
    
    def parse_detail_data(self, response):
        # TODO: Should yield return.
        yield self.get_book_item(response)

        for chapter in self.get_book_catalog(response):
            yield Request(chapter["ref_url"], self.parse_chapter_data)

    def get_book_item(self, response):
        return {}

    def get_book_catalog(self, response):
        return []

    def parse_chapter_data(self, response):
        html_script_tag = response.xpath(
            "//script[contains(text(), 'var qTcms_S_m_murl_e=')]"
        ).get()

        qTcms_S_m_murl_e = eval_js_variable("qTcms_S_m_murl_e", html_script_tag)
        
        if not qTcms_S_m_murl_e:
            self.logger.error("无法解析章节...")
            return

        qTcms_obj = QTcmsObject(
            qTcms_Cur=eval_js_variable("qTcms_Cur", html_script_tag),
            qTcms_S_m_id=eval_js_variable("qTcms_S_m_id", html_script_tag),
            qTcms_S_p_id=eval_js_variable("qTcms_S_p_id", html_script_tag),
            qTcms_S_m_name=eval_js_variable("qTcms_S_m_name", html_script_tag),
            qTcms_S_classid1pinyin=eval_js_variable(
                "qTcms_S_classid1pinyin", html_script_tag
            ),
            qTcms_S_titlepinyin=eval_js_variable(
                "qTcms_S_titlepinyin", html_script_tag
            ),
            qTcms_S_m_playm=eval_js_variable("qTcms_S_m_playm", html_script_tag),
            qTcms_S_m_mhttpurl=eval_js_variable("qTcms_S_m_mhttpurl", html_script_tag),
            qTcms_S_m_murl_e=qTcms_S_m_murl_e,
            qTcms_S_m_murl_e2=eval_js_variable("qTcms_S_m_murl_e2", html_script_tag),
            qTcms_S_m_murl_e3=eval_js_variable("qTcms_S_m_murl_e3", html_script_tag),
            qTcms_Pic_nextArr=eval_js_variable("qTcms_Pic_nextArr", html_script_tag),
            qTcms_Pic_backArr=eval_js_variable("qTcms_Pic_backArr", html_script_tag),
            qTcms_Pic_curUrl=eval_js_variable("qTcms_Pic_curUrl", html_script_tag),
            qTcms_Pic_nextUrl=eval_js_variable("qTcms_Pic_nextUrl", html_script_tag),
            qTcms_Pic_nextUrl_Href=eval_js_variable(
                "qTcms_Pic_nextUrl_Href", html_script_tag
            ),
            qTcms_Pic_len=eval_js_variable("qTcms_Pic_len", html_script_tag),
            qTcms_Pic_backUrl=eval_js_variable("qTcms_Pic_backUrl", html_script_tag),
            qTcms_Pic_backUrl_Href=eval_js_variable(
                "qTcms_Pic_backUrl_Href", html_script_tag
            ),
            qTcms_Pic_Cur_m_id=eval_js_variable("qTcms_Pic_Cur_m_id", html_script_tag),
            qTcms_Pic_m_if=eval_js_variable("qTcms_Pic_m_if", html_script_tag),
            qTcms_Pic_m_status2=eval_js_variable(
                "qTcms_Pic_m_status2", html_script_tag
            ),
            qTcms_m_moban=eval_js_variable("qTcms_m_moban", html_script_tag),
            qTcms_m_indexurl=eval_js_variable("qTcms_m_indexurl", html_script_tag),
            qTcms_m_webname=eval_js_variable("qTcms_m_webname", html_script_tag),
            qTcms_m_weburl=fmt_url_domain(eval_js_variable("qTcms_m_weburl", html_script_tag)),
            qTcms_m_playurl=fmt_url_path(eval_js_variable("qTcms_m_playurl", html_script_tag)),
            qTcms_m_url=fmt_url_path(eval_js_variable("qTcms_m_url", html_script_tag)),
            qTcms_S_show_1=eval_js_variable("qTcms_S_show_1", html_script_tag),
            qTcms_S_ifpubu=eval_js_variable("qTcms_S_ifpubu", html_script_tag),
        )

        image_urls = []

        orig_url_list = base64.b64decode(qTcms_S_m_murl_e).decode().split("$qingtiandy$")

        for index, orig_url in enumerate(orig_url_list):
            img_url = self.parse_img_url(orig_url, qTcms_obj)
            img_name = str(index).zfill(3) + ".jpg"
            img = Image(
                name=img_name,
                url=img_url,
                file_path=None,
                http_headers=None,
            )
            image_urls.append(img)
        
        chapter = MangaChapter(
            name=qTcms_obj.qTcms_S_m_playm,
            ref_url=response.url,
            image_urls=image_urls,
            page_size=len(image_urls),
            rel_m_id=qTcms_obj.qTcms_m_weburl + qTcms_obj.qTcms_m_url,
            rel_m_title=qTcms_obj.qTcms_S_m_name
        )

        yield chapter

    def parse_img_url(self, orig_url, qTcms_obj):
        if orig_url.startswith("/"):
            # If `orig_url` is image file path, we only need provide image server address.
            img_base_url = self.img_base_url or eval_js_variable("qTcms_m_weburl", hmtl.text)
            return img_base_url + orig_url
        elif qTcms_obj.qTcms_Pic_m_if != "2":
            orig_url = (
                orig_url.replace("?", "a1a1").replace("&", "b1b1").replace("%", "c1c1")
            )

            try:
                qTcms_S_m_mhttpurl = base64.b64decode(
                    qTcms_obj.qTcms_S_m_mhttpurl
                ).decode()
                return (
                    qTcms_obj.qTcms_m_indexurl
                    + "statics/pic/?p="
                    + orig_url
                    + "&picid="
                    + qTcms_obj.qTcms_S_m_id
                    + "&m_httpurl="
                    + qTcms_S_m_mhttpurl
                )
            except:
                self.logger.error("无法解析章节图片...")
            return None
        else:
            return None