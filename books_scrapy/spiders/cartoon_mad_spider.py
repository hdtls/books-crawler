import scrapy
import os
import re
from books_scrapy.items import Manga
from books_scrapy.items import MangaChapter
from books_scrapy.items import Image

class CartoonMadSpider(scrapy.Spider):
    name = "cartoonmad"
    allowed_domains = ["cartoonmad.com"]
    base_url = "https://www.cartoonmad.com"
    start_urls = []

    custom_settings = {
        'MEDIA_ALLOW_REDIRECTS': True,
    }

    def __init__(self, **kwargs):
        super(CartoonMadSpider, self).__init__(**kwargs)
        
        id_list = getattr(self, "list", None)

        # Make sure input is valid. 
        if id_list is None or id_list.strip() == "":
            return

        for m_id in id_list.split(','):
            url = self.base_url + "/comic/" + m_id + ".html"
            
            # Ignore duplicate url.
            if url not in self.start_urls:
                self.start_urls.append(url)

    def parse(self, response):
        m_id = response.url.split("/")[-1].split(".")[0]
        
        # Handling missing chapters.
        invalid_id_list = ["2500"]
        if m_id in invalid_id_list:
            return

        # Format string using utf8 encoding.
        m_name = str(response.css('title::text').get()[:-14].strip().replace('?', '').strip())

        # tr_list = response.css("td:nth-child(2) tr:nth-child(4) tr:nth-child(2)")
      
        # m_cover_url = self.base_url + tr_list[1].css("img::attr(src)").get()
        # m_categories = tr_list.css("tr:nth-child(3) a::text").get()
        # m_authors = tr_list.css("tr:nth-child(5) td::text").get().strip()[6:].split(",")
        # m_excerpt = str(response.css("fieldset td::text").get().strip())

        td_list = response.css("fieldset")[1].css("tr > td")

        for index, td in enumerate(td_list):
            c_name = td.css("a::text").get()
            if c_name is None:
                continue
            c_id = c_name.split(" ")[1]
            c_page_size = ""
            
            # Handing page fault.
            if m_id == "1893":
                if index == 0:
                    c_page_size = "11"
                elif index == 1:
                    c_page_size = "21"
            elif m_id == "3908":
                if index == 0:
                    c_page_size = "11"
            else:        
                c_page_size = td.css("font::text").get()[1:-2]

            c_url = self.base_url + td.css("a::attr(href)").get()

            # Get images store from settings.
            img_dir_path = self.settings["IMAGES_STORE"]
            img_dir_path = img_dir_path + "/" + self.name + "/" + m_id + '_' + m_name + '/' + c_name

            # Check whether file exists at `path` and file size equal to `c_page_size` to
            # skip duplicate download operation. 
            if os.path.exists(img_dir_path) and (int(c_page_size) == len(os.listdir(img_dir_path))):
                continue

            if c_id == "001":
                yield scrapy.Request(c_url, meta={"m_id": m_id, "c_name": c_name, "c_id": c_id, "c_page_size": c_page_size, "img_dir_path": img_dir_path}, callback=self.__page_parse)

    def __page_parse(self, response):
        # Hard code ad fixing.
        if '漫畫讀取中' in response.text:
            pattern = '''var link = '(.*?)';'''
            res = re.search(pattern, response.text)
            c_url = res[1]
            yield scrapy.Request(c_url, meta=response.meta, callback=self.__page_parse)
            return

        urls = response.css("img::attr(src)").getall()

        # https://www.cartoonmad.com/comic/comicpic.asp?file=/4695/000/001
        # https://www.cartoonmad.com/home75378/4695/000/001.jpg
        # https://www.cartoonmad.com/comic/comicpic.asp?file=/3080/001/001&rimg=1
        # https://web3.cartoonmad.com/home13712/3080/001/001.jpg

        url_prefix = ''
        url_suff = ""

        # Placeholder image url list.
        p_urls = [
            'https://www.cartoonmad.com/image/rad1.gif',
            'https://www.cartoonmad.com/image/panen.png',
            'https://www.cartoonmad.com/image/rad.gif'
        ]

        for url in urls:
            if url in p_urls:
                # Skip invalid manga image url.
                continue
            if "cc.fun8.us" in url:
                # Skip invalid manga image url.
                continue
            if "comicpic.asp" in url:
                url_prefix = "https://www.cartoonmad.com/comic/comicpic.asp?file=/"
                if '&rimg=1' in url:
                    url_suff = '&rimg=1'
                break
            elif 'cartoonmad' in url:
                url_splits = image_url.split('/')
                url_prefix = url_splits[0] + '//' + url_splits[2] + '/' + url_splits[3] + '/'
                url_suff = ".jpg"
                break

        # Perform chapter download operation.
        # https://web.cartoonmad.com/c37sn562e81/3899/001/010.jpg
        # https://www.cartoonmad.com/comic/comicpic.asp?file=/8726/001/002

        chapter = MangaChapter()
        chapter["name"] = response.meta["c_name"]

        image_list = []
        for page in range(1, int(response.meta["c_page_size"]) + 1):
            image_name = str(page).zfill(3)

            http_headers = {
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
                "DNT": "1",
                "Host": "www.cartoonmad.com",
                "Referer": response.url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
            }

            image = Image(
                name = image_name + '.jpg',
                file_path = response.meta["img_dir_path"] + '/' + image_name + '.jpg',
                url = url_prefix + response.meta["m_id"] + '/' + response.meta["c_id"] + '/' + image_name + url_suff,
                http_headers = http_headers
            )

            image_list.append(image)

        chapter["image_urls"] = image_list

        yield chapter