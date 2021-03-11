# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Manga(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    alias = scrapy.Field()
    cover_image = scrapy.Field()
    background_image = scrapy.Field()
    promo_image = scrapy.Field()
    authors = scrapy.Field()
    status = scrapy.Field()
    categories = scrapy.Field()
    excerpt = scrapy.Field()
    area = scrapy.Field()
    ref_url = scrapy.Field()


class Image(scrapy.Item):
    name = scrapy.Field()
    file_path = scrapy.Field()
    url = scrapy.Field()
    http_headers = scrapy.Field()
    size = scrapy.Field()


class MangaChapter(scrapy.Item):
    name = scrapy.Field()
    ref_url = scrapy.Field()
    images = scrapy.Field()
    image_urls = scrapy.Field()
    page_size = scrapy.Field()
    rel_m_id = scrapy.Field()
    rel_m_title = scrapy.Field()
