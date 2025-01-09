import os
from csvpath.managers.results.result import Result


class VarUtility:
    @classmethod
    def get_value_pairs(cls, result: Result, directive: str) -> list[tuple[str, str]]:
        #
        # gets values like key: a > b, c > d
        # the return is [(a,b),(b,c)]
        # the values of b and d can be the names of env vars -- recognized by being in
        # all caps -- which will be subsituted. if the presumed env var name doesn't
        # result in a value the presumed name is returned.
        #
        if directive is None:
            return None
        v = result.csvpath.metadata.get(directive)
        if v is None:
            return None
        v = f"{v}"
        vs = v.split(",")
        pairs = []
        for v in vs:
            pair = VarUtility.create_pair(result, v)
            pairs.append(pair)
        return pairs

    @classmethod
    def create_pair(self, result: Result, v: str) -> tuple[str, str]:
        v = v.strip()
        i = v.find(">")
        if i == -1:
            return (v, None)
        v1 = v[0:i]
        v1 = v1.strip()
        v2 = v[i + 1 :]
        v2 = v2.strip()

        v3 = VarUtility.value_or_var_value(result, v2)
        if v3 is not None:
            v2 = v3.strip()
        return (v1, v2)

    @classmethod
    def get_value(cls, result: Result, v: str):
        if v is None:
            return None
        v = result.csvpath.metadata.get(v)
        if v is None:
            return None
        if isinstance(v, str):
            v = VarUtility.value_or_var_value(result, v)
        return v

    @classmethod
    def value_or_var_value(cls, result: Result, v: str) -> ...:
        #
        # do any var swapping first
        i = v.find("var|")
        if i != -1:
            v2 = v[4:]
            v2 = v2.strip()
            if v2 in result.csvpath.variables:
                v2 = result.csvpath.variables[v2]
            v = v2
        #
        # if the value is ALL CAPS check if it is an
        # env var.
        if v and v.isupper():
            v2 = v.strip()
            v2 = os.getenv(v2)
            if v2 is not None:
                v = v2.strip()
        return v

    @classmethod
    def get_str(cls, result: Result, directive: str):
        v = VarUtility.get_value(result, directive)
        v = f"{v}"
        v = v.strip()
        return v

    @classmethod
    def get_int(cls, result: Result, directive: str):
        v = VarUtility.get_value(result, directive)
        return VarUtility.to_int(v)

    @classmethod
    def to_int(cls, v) -> int:
        if not isinstance(v, int):
            v = f"{v}"
            v = v.strip()
            try:
                v = int(v)
            except ValueError:
                return None
        return v

    @classmethod
    def get_bool(cls, result: Result, directive: str) -> bool:
        v = VarUtility.get_value(result, directive)
        return VarUtility.is_true(v)

    @classmethod
    def is_true(cls, v) -> bool:
        if v is None:
            return False
        if v is True or v is False:
            return v
        if v == 0 or v == 1:
            return bool(v)
        v = f"{v}".lower().strip()
        if v == "true" or v == "yes":
            return True
        if v == "false" or v == "no" or v == "null" or v == "none":
            return False
        return False
