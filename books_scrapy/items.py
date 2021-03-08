# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Manga(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    cover_image = scrapy.Field()
    status = scrapy.Field()
    authors = scrapy.Field()
    categories = scrapy.Field()
    excerpt = scrapy.Field()
    chapters = scrapy.Field()


class Image(scrapy.Item):
    name = scrapy.Field()
    file_path = scrapy.Field()
    url = scrapy.Field()
    http_headers = scrapy.Field()
    size = scrapy.Field()


class MangaChapter(scrapy.Item):
    identifier = scrapy.Field()
    name = scrapy.Field()
    ref_url = scrapy.Field()
    images = scrapy.Field()
    image_urls = scrapy.Field()
    page_size = scrapy.Field()
    parent_id = scrapy.Field()
    parent_name = scrapy.Field()


class CartoonMadManga(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    image_urls = scrapy.Field()

    imgfolder = scrapy.Field()
    # 设置header
    imgheaders = scrapy.Field()
    pass