from books_scrapy.utils.coding import DecodingError
from scrapy.exceptions import DropItem


class ValidatePipeline:
    def __init__(self, crawler):
        self.settings = crawler.settings

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item, spider):
        if hasattr(item, "validate"):
            try:
                item.validate()
            except DecodingError as e:
                raise DropItem(str(e))
        else:
            raise DropItem("Unsupported item.", item)

        return item
