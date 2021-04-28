from books_scrapy.items import (
    Manga,
    Author,
    MangaArea,
    MangaCategory,
    MangaChapter,
    PHAsset,
)
from itemloaders.utils import arg_to_iter
from itemloaders.processors import Compose, Identity, MapCompose, TakeFirst
from scrapy.loader import ItemLoader


def _splitting(value):
    if not value:
        return []
    separator = None
    if "," in value:
        separator = ","
    elif " " in value:
        separator = " "
    elif "x" in value:
        separator = "x"
    return list(map(lambda e: e.strip(), value.split(separator)))


class MangaLoader(ItemLoader):

    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    default_item_class = Manga

    cover_image_in = MapCompose(lambda url: dict(ref_url=url))
    schedule_in = MapCompose(lambda s: 1 if "完结" in s[0] else 0)
    authors_in = MapCompose(_splitting, lambda name: Author(name=name))
    authors_out = Identity()
    ref_urls_out = Identity()
    area_in = MapCompose(lambda name: MangaArea(name=name))
    aliases_in = MapCompose(_splitting)
    background_image_in = cover_image_in
    promo_image_in = cover_image_in
    categories_in = MapCompose(_splitting, lambda name: MangaCategory(name=name))
    categories_out = Identity()


class ChapterLoader(ItemLoader):

    default_output_processor = TakeFirst()
    default_item_class = MangaChapter

    ref_urls_out = Identity()
    cover_image_in = MangaLoader.cover_image_in
    asset_out = Compose(
        lambda urls: PHAsset(files=[dict(ref_url=url) for url in arg_to_iter(urls)])
    )
