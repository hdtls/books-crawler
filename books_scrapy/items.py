# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Manga(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    image_url = scrapy.Field()
    status = scrapy.Field()
    recently_updated = scrapy.Field()
    authors = scrapy.Field()
    categories = scrapy.Field()
    excerpt = scrapy.Field()
    chapters = scrapy.Field()
    
class Chapter(scrapy.Item):
    name = scrapy.Field()
    image_urls = scrapy.Field()