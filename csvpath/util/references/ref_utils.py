# pylint: disable=C0114
from datetime import timedelta, timezone, datetime
from csvpath.matching.util.expression_utility import ExpressionUtility
from .reference_parser import ReferenceParser


class ReferenceUtility:
    @classmethod
    def by_day(cls, run_dir: str) -> str:
        pointer = cls.pointer(run_dir)
        run = cls.not_pointer(run_dir)
        if run == "today":
            ret = cls.translate_today()
            if pointer is not None:
                ret = f"{ret}:{pointer}"
        elif run == "yesterday":
            ret = cls.translate_yesterday()
            if pointer is not None:
                ret = f"{ret}:{pointer}"
        else:
            ret = run_dir
        return ret

    @classmethod
    def translate_today(cls) -> str:
        d = datetime.now().astimezone(timezone.utc)
        ret = f"{d.strftime('%Y')}-{d.strftime('%m')}-{d.strftime('%d')}_"
        return ret

    @classmethod
    def translate_yesterday(cls) -> str:
        d = datetime.now().astimezone(timezone.utc)
        d = d - timedelta(days=1)
        ret = f"{d.strftime('%Y')}-{d.strftime('%m')}-{d.strftime('%d')}_"
        return ret

    @classmethod
    def is_day(cls, name: str) -> bool:
        if name.find(":"):
            name = name[0 : name.find(":")]
        return name in ["yesterday", "today"]

    @classmethod
    def pointer(cls, name: str, default: str = None) -> str:
        if name is None:
            return None
        if name.find(":") == -1:
            return default
        return name[name.find(":") + 1 :]

    @classmethod
    def not_pointer(cls, name: str) -> str:
        if name is None:
            return None
        if name.find(":") == -1:
            return name
        return name[0 : name.find(":")]

    @classmethod
    def bare_index_if(cls, name: str) -> int | None:
        name = name.strip()
        if name[0] != ":":
            return None
        name = name[1:]
        if not ExpressionUtility.is_number(name):
            return None
        name = ExpressionUtility.to_int(name)
        if isinstance(name, int):
            return name
        return None
