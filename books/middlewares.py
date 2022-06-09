# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

"""This module contains the ``PlaywrightMiddleware`` scrapy middleware"""

import requests
from cf_clearance import sync_stealth
from playwright.sync_api import sync_playwright
from scrapy import signals
from scrapy.http import HtmlResponse


class PlaywrightMiddleware:
    """Playwright middleware handling the requests using playwright"""

    def __init__(self, executable_path):
        """Initialize the playwright
        Parameters
        ----------
        executable_path: str
            The path of the executable binary of the playwright
        """
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            executable_path=executable_path, headless=False
        )
        self.cookies = {}
        self.headers = {}

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        executable_path = crawler.settings.get("PLAYWRIGHT_EXECUTABLE_PATH")

        middleware = cls(executable_path=executable_path)

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the playwright if applicable"""

        if not request.meta.get("playwright"):
            return

        headers = request.headers.to_unicode_dict()
        headers.update(self.headers)
        cookies = request.cookies
        cookies.update(self.cookies)

        response = requests.request(
            method=request.method, url=request.url, headers=headers, cookies=cookies
        )
        # If status_code is equals to 200 then update cookies
        if response.status_code == 200:
            body = response.content
            return HtmlResponse(response.url, body=body, encoding=response.encoding, request=request)
        else:
            page = self.browser.new_page()
            sync_stealth(page, pure=True)
            page.goto(request.url, wait_until="domcontentloaded")

            # TODO: fetch selector from request meta
            page.wait_for_selector("div.all_data_list", timeout=60000)

            # Update cookies
            for cookie in page.context.cookies():
                if cookie.get("name") == "cf_clearance":
                    self.cookies["cf_clearance"] = cookie.get("value")

            # Update userAgent
            self.headers["user-agent"] = page.evaluate("() => navigator.userAgent")
            body = str.encode(page.content(), encoding="utf-8")
            request.meta["page"] = page

            return HtmlResponse(page.url, body=body, encoding="utf-8", request=request)

    def spider_closed(self):
        """Shutdown the browser when spider is closed"""
        self.browser.close()
        self.playwright.stop()
