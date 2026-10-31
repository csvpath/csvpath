import re

from .regex_utility import RegexUtility as reut


class AllowListSet:
    """the allow lists a csvpath uses. An occurrence is allowed (not
    reported) if its text exactly equals a text allow list entry, ignoring
    case, or fully matches an allow list regex. Allow lists apply to every
    identifier, custom and managed.

    We compare against the occurrence text, not the whole cell: Macie's
    docs only require that the text not be split across cells (to confirm
    in the fidelity scan against real Macie).
    """

    def __init__(self) -> None:
        self.names = []
        self.words = set()
        self.patterns: list[re.Pattern] = []

    def add_regex(self, *, name: str, pattern: str) -> None:
        self._check_name(name=name)
        self.patterns.append(reut.compile(pattern=pattern))
        self.names.append(name)

    def add_words(self, *, name: str, entries: list[str]) -> None:
        self._check_name(name=name)
        if not isinstance(entries, list):
            raise TypeError(f"entries must be a list, not {type(entries)}")
        for entry in entries:
            if not isinstance(entry, str):
                raise TypeError(f"Allow list {name} has a non-str entry: {entry!r}")
            if entry.strip() != "":
                self.words.add(entry.lower())
        self.names.append(name)

    def allows(self, *, text: str) -> bool:
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        if text.lower() in self.words:
            return True
        return any(p.fullmatch(text) for p in self.patterns)

    def _check_name(self, *, name: str) -> None:
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("Allow list name must be a non-empty str")
        if name in self.names:
            raise ValueError(f"Allow list {name} added twice")
