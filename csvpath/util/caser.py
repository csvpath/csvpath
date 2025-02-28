import os


class Caser:
    @classmethod
    def isupper(cls, s: str) -> bool:
        if s is None:
            return False
        if not isinstance(s, str):
            return False
        s = s.strip()
        num = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
        ]
        allnum = True
        for c in s:
            if c == "_":
                allnum = False
                continue
            if not c.isalnum():
                return False
            if c in num:
                continue
            if not c.isupper():
                return False
            allnum = False
        return not allnum
