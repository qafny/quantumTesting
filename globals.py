from typing import List


class TagProcessor:

    _shared = {}

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        obj.__dict__ = cls._shared

        return obj

    def set_tags(self, tags: List[str]):
        self.tags = tags

    def remove_prefixed_hadamards(self):
        return "parse_rph" in self.tags

    def remove_suffixed_hadamards(self):
        return "parse_rsh" in self.tags

    def remove_measure(self):
        return "parse_rm" in self.tags
