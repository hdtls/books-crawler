from books.items import (
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


def splitting(value):
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

    authors_in = MapCompose(splitting, str.strip, lambda name: Author(username=name))
    authors_out = Identity()
    area_in = MapCompose(str.strip, lambda name: MangaArea(name=name))
    aliases_in = MapCompose(splitting, str.strip)
    background_image_in = MapCompose(str.strip, lambda url: dict(ref_url=url))
    categories_in = MapCompose(str.strip, lambda name: MangaCategory(name=name))
    categories_out = Identity()
    cover_image_in = background_image_in
    promo_image_in = background_image_in
    ref_urls_out = Identity()
    schedule_in = MapCompose(lambda s: 1 if "完结" in s else 0)


class ChapterLoader(ItemLoader):

    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    default_item_class = MangaChapter

    ref_urls_out = Identity()
    cover_image_in = MangaLoader.cover_image_in
    assets_in = Compose(
        lambda val: [
            PHAsset(files=[dict(ref_url=url) for url in arg_to_iter(urls)])
            for urls in [arg_to_iter(val)]
            if urls
        ]
    )
