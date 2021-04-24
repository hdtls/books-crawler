from typing import Iterable, Optional, TypeVar


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
