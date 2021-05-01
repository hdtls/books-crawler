# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

from books_scrapy.utils.misc import formatted_meta, revert_formatted_meta
from scrapy_redis.spiders import RedisSpider


class BookSpider(RedisSpider):
    """Base class for book spiders."""

    def parse(self, response, **kwargs):
        return self.parse_detail_data(response)

    def parse_detail_data(self, response):
        """Parse detail page data (e.g. book info and catalog)."""

        book_info = self.get_detail(response)

        catalog = self.get_catalog(response)
        if not catalog:
            return

        yield book_info

        yield from response.follow_all(
            catalog,
            self._parse_chapter_data,
            meta=formatted_meta(book_info),
        )

    def get_detail(self, response):
        """
        Get book information from `response` object.
        - Parameter response: Source data.
        - Returns: Book info model.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_detail is not implemented"
        )

    def get_catalog(self, response):
        """
        Get book catalog from `response` object.
        - Parameter response: Source data.
        - Retures: Book catalog
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_catalog is not implemented"
        )

    def _parse_chapter_data(self, response):
        book_info = revert_formatted_meta(response.meta)
        return self.parse_chapter_data(response, book_info)

    def parse_chapter_data(self, response, book_info):
        """
        Parse chapter page data. Override this function to provide parsing logic.
        All response have meta which value is info of this book.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.parse_chapter_data is not implemented."
        )
