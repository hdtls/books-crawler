# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import os
import scrapy

from books_scrapy.items import Manga
from books_scrapy.items import MangaChapter
from books_scrapy.utils import get_img_store
from pathlib import Path

class Spider(scrapy.Spider):
    """Base class for book spiders."""

    def parse(self, response, **kwargs):
        return self.parse_detail_data(response)

    def parse_detail_data(self, response):
        """Parse detail page data e.g., book info and catalog."""

        book_info = self.get_book_info(response)
        yield book_info

        book_catalog = self.get_book_catalog(response)

        file_path = get_img_store(self.settings, self.name, book_info.name)

        if Path(file_path).exists() and len(os.listdir(file_path)) >= len(book_catalog):
            # File size in `file_path` is greater than or equal to catalog size.
            # all catalog already been crawled.
            return

        for entry in book_catalog:
            yield scrapy.Request(entry.ref_url, self.parse_chapter_data)

    def get_book_info(self, response) -> Manga:
        """
        Get book information from `response` object.
        - Parameter response: Source data.
        - Returns: Book info model.
        """
        raise NotImplementedError(f'{self.__class__.__name__}.get_book_info is not implemented')
    
    def get_book_catalog(self, response) -> list[MangaChapter]:
        """
        Get book catalog from `response` object.
        - Parameter response: Source data.
        - Retures: Book catalog
        """
        raise NotImplementedError(f'{self.__class__.__name__}.get_book_catalog is not implemented')

    def parse_chapter_data(self, response):
        """Parse chapter page data. Override this function to provide parsing logic."""
        raise NotImplementedError(f'{self.__class__.__name__}.parse_chapter_data is not implemented.')