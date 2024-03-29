import base64

from books.items import *
from books.loaders import ChapterLoader, MangaLoader
from books.spiders import BookSpider
from books.utils.misc import eval_js_variable


class The517MangaSpider(BookSpider):
    name = "www.517manhua.com"
    # start_urls = ["http://www.517manhua.com/xuanhuan/jiesuomoshide99genvzhu/"]
    qTcms_m_indexurl = "http://images.yiguahai.com"

    def get_detail(self, response):
        loader = MangaLoader(response=response)

        loader.add_xpath(
            "cover_image", "//div[contains(@class, 'mh-date-bgpic')]//img/@src"
        )
        loader.add_value("ref_urls", [response.url])

        nested_loader = loader.nested_xpath("//div[contains(@class, 'mh-date-info')]")
        nested_loader.add_xpath(
            "name", "./div[contains(@class, 'mh-date-info-name')]//a/text()"
        )
        nested_loader.add_xpath(
            "excerpt", "./div[contains(@class, 'work-introd')]//p/text()"
        )
        nested_loader.add_xpath(
            "authors", "./p[contains(@class, 'works-info-tc')]//em/a/text()"
        )
        nested_loader.add_xpath(
            "schedule",
            "./p[contains(@class, 'works-info-tc')][position()=2]/span[last()]/em/text()",
        )

        return loader.load_item()

    def get_catalog(self, response):
        return response.xpath("//ul[@id='mh-chapter-list-ol-0']/li/a")

    def parse_chapter_data(self, response, book_info):
        script_tag = response.xpath(
            "//script[contains(text(), 'var qTcms_S_m_murl_e=')]"
        ).get()

        qTcms_S_m_murl_e = eval_js_variable("qTcms_S_m_murl_e", script_tag)

        if not qTcms_S_m_murl_e:
            return
            
        qTcms_S_m_murl_e = base64.b64decode(qTcms_S_m_murl_e).decode()

        orig_url_list = qTcms_S_m_murl_e.split("$qingtiandy$")
        qTcms_S_m_name=eval_js_variable("qTcms_S_m_name", script_tag),
        qTcms_S_m_playm=eval_js_variable("qTcms_S_m_playm", script_tag),
        if not isinstance(orig_url_list):
            self.logger.error(f"Failed to parse <{qTcms_S_m_name}> {qTcms_S_m_playm} refer: {response.url}")
            return

        config = QTCMSConfiguration(
            qTcms_Cur=eval_js_variable("qTcms_Cur", script_tag),
            qTcms_S_m_id=eval_js_variable("qTcms_S_m_id", script_tag),
            qTcms_S_p_id=eval_js_variable("qTcms_S_p_id", script_tag),
            qTcms_S_m_name=qTcms_S_m_name,
            qTcms_S_classid1pinyin=eval_js_variable(
                "qTcms_S_classid1pinyin", script_tag
            ),
            qTcms_S_titlepinyin=eval_js_variable("qTcms_S_titlepinyin", script_tag),
            qTcms_S_m_playm=qTcms_S_m_playm,
            qTcms_S_m_mhttpurl=eval_js_variable("qTcms_S_m_mhttpurl", script_tag),
            qTcms_S_m_murl_e=qTcms_S_m_murl_e,
            qTcms_S_m_murl_e2=eval_js_variable("qTcms_S_m_murl_e2", script_tag),
            qTcms_S_m_murl_e3=eval_js_variable("qTcms_S_m_murl_e3", script_tag),
            qTcms_Pic_nextArr=eval_js_variable("qTcms_Pic_nextArr", script_tag),
            qTcms_Pic_backArr=eval_js_variable("qTcms_Pic_backArr", script_tag),
            qTcms_Pic_curUrl=eval_js_variable("qTcms_Pic_curUrl", script_tag),
            qTcms_Pic_nextUrl=eval_js_variable("qTcms_Pic_nextUrl", script_tag),
            qTcms_Pic_nextUrl_Href=eval_js_variable(
                "qTcms_Pic_nextUrl_Href", script_tag
            ),
            qTcms_Pic_len=eval_js_variable("qTcms_Pic_len", script_tag),
            qTcms_Pic_backUrl=eval_js_variable("qTcms_Pic_backUrl", script_tag),
            qTcms_Pic_backUrl_Href=eval_js_variable(
                "qTcms_Pic_backUrl_Href", script_tag
            ),
            qTcms_Pic_Cur_m_id=eval_js_variable("qTcms_Pic_Cur_m_id", script_tag),
            qTcms_Pic_m_if=eval_js_variable("qTcms_Pic_m_if", script_tag),
            qTcms_Pic_m_status2=eval_js_variable("qTcms_Pic_m_status2", script_tag),
            qTcms_m_moban=eval_js_variable("qTcms_m_moban", script_tag),
            qTcms_m_indexurl=eval_js_variable("qTcms_m_indexurl", script_tag),
            qTcms_m_webname=eval_js_variable("qTcms_m_webname", script_tag),
            qTcms_m_weburl=eval_js_variable("qTcms_m_weburl", script_tag),
            qTcms_m_playurl=eval_js_variable("qTcms_m_playurl", script_tag),
            qTcms_m_url=eval_js_variable("qTcms_m_url", script_tag),
            qTcms_S_show_1=eval_js_variable("qTcms_S_show_1", script_tag),
            qTcms_S_ifpubu=eval_js_variable("qTcms_S_ifpubu", script_tag),
        )

        loader = ChapterLoader()
        loader.add_value("name", config.qTcms_S_m_playm)
        loader.add_value("ref_urls", [response.url])
        loader.add_value(
            "assets",
            list(
                map(
                    lambda url: self._replace_img_url_hostname(url, config),
                    orig_url_list,
                )
            ),
        )

        item = loader.load_item()
        item.manga = book_info
        yield item

    def _replace_img_url_hostname(self, orig_url, config):
        if orig_url.startswith("/"):
            # If `orig_url` is image file path, we only need provide image server address.
            img_base_url = self.img_base_url or config.qTcms_m_weburl
            img_base_url = (
                img_base_url[:-1] if img_base_url.endswith("/") else img_base_url
            )
            return img_base_url + orig_url
        elif config.qTcms_Pic_m_if != "2":
            orig_url = (
                orig_url.replace("?", "a1a1").replace("&", "b1b1").replace("%", "c1c1")
            )

            try:
                qTcms_S_m_mhttpurl = base64.b64decode(
                    config.qTcms_S_m_mhttpurl
                ).decode()
                return (
                    (self.qTcms_m_indexurl + "/" or config.qTcms_m_indexurl)
                    + "statics/pic/?p="
                    + orig_url
                    + "&picid="
                    + config.qTcms_S_m_id
                    + "&m_httpurl="
                    + qTcms_S_m_mhttpurl
                )
            except:
                return None
        else:
            return None
