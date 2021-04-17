import re
import json
from typing import Iterable, Optional, TypeVar


def fmt_label(label):
    return label.strip() if isinstance(label, str) else ""


def fmt_url_domain(domain):
    if not isinstance(domain, str):
        return None
    return domain[:-1] if domain.endswith("/") else domain


def fmt_url_path(path):
    if not isinstance(path, str):
        return None
    return path if path.startswith("/") else path[1:]


def format_meta(arg):
    return {"__meta__": arg}


def revert_formatted_meta(arg):
    return arg["__meta__"]


def eval_js_variable(label, text):
    match = re.findall(r"var %s ?= ?(.*?);" % (label), text)
    if not match:
        return None
    return json.loads(match[0])


def list_extend(lhs, rhs):
    lhs = lhs or []
    rhs = rhs or []
    return list(set(lhs + rhs)) or None


_T = TypeVar("_T")
class IterDiff:
    def __init__(self, orig: Iterable[_T], new: Iterable[_T]):
        self.orig = orig
        self.new = new

    @property
    def added(self):
        return filter(lambda x: x not in self.orig, self.new)

    @property
    def removed(self):
        return filter(lambda x: x not in self.new, self.orig)


def iter_diff(__orig: Optional[Iterable[_T]], __new: Optional[Iterable[_T]]):
    __new = __new or []
    return IterDiff(orig=__orig or [], new=__new or [])
