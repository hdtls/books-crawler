import dataclasses
import typing

from typing import Any


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
