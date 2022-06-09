from books.utils.typing_inspect import CodingError, typing_inspect
from scrapy.exceptions import DropItem


class ValidatePipeline:
    def __init__(self, crawler):
        self.settings = crawler.settings

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item, spider):
        try:
            typing_inspect(item)
        except CodingError as e:
            raise DropItem(str(e))
        return item
