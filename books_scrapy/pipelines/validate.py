from books_scrapy.items import Manga, MangaChapter
import logging

from scrapy.exceptions import DropItem

class ValidatePipeline:
    def __init__(self, crawler):
        self.settings = crawler.settings
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item, spider):
        if isinstance(item, Manga):
            if not (item.name and item.authors and item.excerpt and item.chapters):
                raise DropItem("Invalid manga item missing keys(name, authors, excerpt, chapters).")
            for chapter in item.chapters:
                if not isinstance(chapter, MangaChapter):
                    raise DropItem("Unsupported item.")

                if not (chapter.name and chapter.image_urls):
                    raise DropItem("Invalid manga chapter missing keys(name, image_urls).")
        else:
            raise DropItem("Unsupported item.")
        
        return item
