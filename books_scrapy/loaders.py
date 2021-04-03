from books_scrapy.items import Author, Manga, MangaArea, MangaCategory
from itemloaders.processors import Identity, MapCompose, TakeFirst
from scrapy.loader import ItemLoader


def _make_img(url):
    return dict(url=url, ref_urls=[url]) if url else None


def split_with_space_or_comma(value):
    if not value:
        return []
    separator = None
    if "," in value:
        separator = ","
    elif " " in value:
        separator = " "
    return value.split(separator)


class MangaLoader(ItemLoader):

    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()

    cover_image_in = MapCompose(_make_img)
    schedule_in = MapCompose(lambda s: 1 if "完结" in s[0] else 0)
    authors_in = MapCompose(split_with_space_or_comma, lambda name: Author(name=name))
    authors_out = Identity()
    ref_urls_out = Identity()
    area_in = MapCompose(lambda name: MangaArea(name=name))
    aliases_in = MapCompose(split_with_space_or_comma)
    background_image_in = MapCompose(_make_img)
    promo_image_in = MapCompose(_make_img)
    categories_in = MapCompose(
        split_with_space_or_comma, lambda name: MangaCategory(name=name)
    )
    categories_out = Identity()
