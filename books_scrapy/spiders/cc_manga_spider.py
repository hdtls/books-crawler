import scrapy
from books_scrapy.items import Manga

class CCMangaSpider(scrapy.Spider):
    name = "cc_manga"
    allowed_domains = "https://www.cocomanhua.com"
    # start_urls = ["https://www.cocomanhua.com/show?orderBy=update"]

    # def parse(self, response): 
    #     path_list = response.css("ul.fed-list-info li a::attr(href)").getall()

    #     for path in path_list:
    #         yield scrapy.Request(self.allowed_domains + path, self._manga_detail_parse)
    start_urls = ["https://www.cocomanhua.com/12202"]

    def parse(self, response):
    #     self._manga_detail_parse(response)

    # def _manga_detail_parse(self, response):
        main = response.css("div.fed-main-info .fed-part-case")
        meta = main.css("dl.fed-deta-info")[0]
        info_list = meta.css("dd.fed-deta-content .fed-part-rows li")

        self.log("Parsing...")

        name = meta.css("dd.fed-deta-content h1::text").get()
        image_url = meta.css("dt.fed-deta-images a::attr(data-original)").get()
        status = ""
        authors = []
        recently_updated = ""
        categories = []
        excerpt = ""

        for li in info_list:
            title = li.css("span::text").get()
            if title == "状态":
                status = li.css("a::text").get()
            elif title == "作者":
                authors = li.css("a::text").get().split(",")
            # elif title == "更新":
            elif title == "最新":
                recently_updated = li.css("a::text").get()
            elif title == "类别":
                categories = li.css("a::text").get()
            elif title == "简介":
                excerpt = li.css("div::text").get()
            # else:
            #     print("New case.")

        chapter_urls = main.css("div.all_data_list ul li a::attr(href)").getall()
        # Make chapter order by create date.    
        chapter_urls.reverse()

        # for url in chapter_urls:
        url = chapter_urls[0]
        yield scrapy.Request(self.allowed_domains + url, callback=self._manga_chapter_parse, meta={
            "name": name,
            "image_url": image_url,
            "status": status,
            "authors": authors,
            "recently_updated": recently_updated,
            "categories": categories,
            "excerpt": excerpt
        }, dont_filter=True)

    def _manga_chapter_parse(self, response):
        self.log("Parsing chapter...")
        manga_list = response.css("div.mh_comicpic")

        sorted_list = []
        for li in manga_list:
            self.log(li)
            sorted_list.append((li.css("::attr(p)").get(), li.css("img::attr(src)").get()))
            self.log(sorted_list)

        sorted_list.sort(key=lambda m: m[0])

        manga = Manga()
        manga["name"] = response.meta["name"]
        manga["image_url"] = response.meta["image_url"]
        manga["status"] = response.meta["status"]
        manga["authors"] = response.meta["authors"]
        manga["recently_updated"] = response.meta["recently_updated"]
        manga["categories"] = response.meta["categories"]
        manga["excerpt"] = response.meta["excerpt"]
        manga["chapters"] = sorted_list
        
        self.log(manga)
        yield manga