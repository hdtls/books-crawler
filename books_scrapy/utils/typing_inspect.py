import dataclasses
import typing

from typing import Any, List, Optional


class CodingError(Exception):
    pass


def type_mismatch(path, expectation, reality):
    return CodingError(
        f"typeMismatch({expectation} codingPath: {path} debugDescription: 'Expected to decode {expectation} but found a {type(reality)} instead.')"
    )


def typing_inspect_type(path: str, expectation: type, value: Any):
    if isinstance(value, expectation):
        if hasattr(value, "__validate__"):
            value.__validate__(path)
        else:
            if dataclasses.is_dataclass(value):
                typing_inspect(value, path)
    else:
        raise type_mismatch(path, expectation, value)


def typing_inspect_collection(path: str, expectation: type, value: Any):
    el_expectation = expectation.__args__[0]
    for index, val in enumerate(value):
        typing_inspect_types(f"{path}[{index}]", el_expectation, val)


def _validate_typing_list(path: str, expectation: type, value: Any):
    typing_inspect_type(path, list, value)
    typing_inspect_collection(path, expectation, value)


def _validate_typing_tuple(path: str, expectation: type, value: Any):
    typing_inspect_type(path, tuple, value)
    typing_inspect_collection(path, expectation, value)


def _validate_typing_frozenset(path: str, expectation: type, value: Any):
    typing_inspect_type(path, frozenset, value)
    typing_inspect_collection(path, expectation, value)


def _validate_typing_dict(path: str, expectation: type, value: Any):
    typing_inspect_type(path, dict, value)

    expected_key_type = expectation.__args__[0]
    expected_value_type = expectation.__args__[1]

    for (key, val) in enumerate(value):
        typing_inspect_types(f"{path}.{key}", expectation=expected_key_type, value=key)
        typing_inspect_types(
            f"{path}.{val}", expectation=expected_value_type, value=val
        )


def _validate_typing_callable(path: str, expectation: type, value: Any):
    typing_inspect_type(path, type(lambda a: a), value)


_validate_typing_mappings = {
    "List": _validate_typing_list,
    "Tuple": _validate_typing_tuple,
    "FrozenSet": _validate_typing_frozenset,
    "Dict": _validate_typing_dict,
    "Callable": _validate_typing_callable,
}


def typing_inspect_generic(path, expectation: type, value: Any):
    validate = _validate_typing_mappings.get(expectation._name)
    if validate is not None:
        validate(path, expectation, value)

    if str(expectation).startswith("typing.Union"):
        for type in expectation.__args__:
            typing_inspect_types(path, type, value)

    if str(expectation).startswith("typing.Optional"):
        if value:
            typing_inspect_types(path, expectation.__args__[0], value)


def typing_inspect_types(path: str, expectation: type, value: Any):
    if isinstance(expectation, type):
        typing_inspect_type(path, expectation=expectation, value=value)

    if isinstance(expectation, typing._GenericAlias):
        typing_inspect_generic(path, expectation=expectation, value=value)


def typing_inspect(target, path=None):
    fields = dataclasses.fields(target)

    for field in fields:
        field_name = field.name
        expectation = field.type
        value = getattr(target, field_name)

        typing_inspect_types(
            f"{path or type(target)}.{field_name}", expectation=expectation, value=value
        )


@dataclasses.dataclass
class Author:
    name: str


@dataclasses.dataclass
class MangaArea:
    name: str


@dataclasses.dataclass
class MangaCategory:
    name: str

    def __validate__(self, path=None):
        typing_inspect(self, path)


@dataclasses.dataclass
class PHAsset:
    files: List[dict]

    def __validate__(self, path=None):
        typing_inspect(self, path)


@dataclasses.dataclass
class MangaChapter:
    asset: PHAsset
    optional: Optional[PHAsset] = None

    def __validate__(self, path=None):
        typing_inspect(self, path)


@dataclasses.dataclass
class Manga:
    cover_image: dict
    excerpt: str
    authors: List[Author]
    schedule: int = 0
    ref_urls: Optional[List[str]] = None
    area: Optional[MangaArea] = None
    aliases: Optional[List[str]] = None
    background_image: Optional[dict] = None
    promo_image: Optional[dict] = None
    categories: Optional[List[MangaCategory]] = None
    chapters: Optional[List[MangaChapter]] = None


if __name__ == "__main__":
    # typing_validate(Manga({}, "", None))
    # typing_validate(Manga("str", "", []))
    # typing_validate(Manga({}, "", ["str"]))
    # typing_validate(Manga({}, "", [None]))
    # typing_validate(Manga({}, "", [Author("name")]))
    # typing_validate(Manga({}, "", [Author("name")], aliases=["1"]))
    # typing_validate(Manga({}, "", [Author("name")], background_image=1))
    # typing_validate(Manga({}, "", [Author("name")], categories=[1]))
    # typing_validate(Manga({}, "", [Author("name")], categories=[MangaCategory(name=1)]))
    typing_inspect(
        Manga(
            {},
            "str",
            [Author("name")],
            categories=[MangaCategory(name="1")],
            chapters=[MangaChapter(asset=PHAsset([{}]), optional=PHAsset([{}]))],
        )
    )
