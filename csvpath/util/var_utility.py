import os
from os import environ
from .config import Config


class VarUtility:

    #
    # finds variables that may be in env vars. does these steps:
    #  1. if env var name passed check for it
    #  2. if None, look in config.ini
    #  3. if None, return default
    #  4. if value found is not isupper return value
    #  5. if value found isupper, check env
    #  6. if env is None, return the uppercase value
    #  7. return the env value
    #
    @classmethod
    def get(
        cls,
        *,
        section: str = None,
        name: str = None,
        env: str = None,
        default=None,
        config: Config = None,
    ) -> str:
        v = None
        if env:
            v = environ.get(env)
        if v is not None:
            return v
        # check config
        if section and name:
            if config is None:
                config = Config()
            v = config.get(section=section, name=name)
        elif section or name:
            if config is None:
                config = Config()
            config.logger.warn(
                "Get var with section or name but not both will not work: %s, %s",
                section,
                name,
            )
        # config val or None
        if v is None:
            return default
        v2 = None
        if cls.isupper(v):
            v2 = environ.get(v)
        return v if v2 is None else v2

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

    @classmethod
    def get_value_pairs(
        cls, *, metadata: dict, variables: dict, key: str, default: str = None
    ) -> list[tuple[str, str]]:
        if key is None:
            return default
        v = metadata.get(key)
        if v is None:
            return default
        v = metadata.get(key)
        return cls.get_value_pairs_from_value(
            metadata=metadata, variables=variables, value=v, default=default
        )

    @classmethod
    def get_value_pairs_from_value(
        cls, *, metadata: dict, variables: dict, value: str, default=None
    ) -> list[tuple[str, str]]:
        #
        # gets values like key: a > b, c > d
        # the return is [(a,b),(b,c)]
        # the values of b and d can be the names of env vars -- recognized by being in
        # all caps -- which will be subsituted. if the presumed env var name doesn't
        # result in a value the presumed name is returned.
        #
        if value is None:
            return default
        value = f"{value}"
        vs = value.split(",")
        pairs = []
        for value in vs:
            pair = VarUtility.create_pair(metadata, variables, value)
            pairs.append(pair)
        return pairs

    @classmethod
    def create_pair(self, mdata: dict, variables: dict, v: str) -> tuple[str, str]:
        v = v.strip()
        i = v.find(">")
        if i == -1:
            return (v, None)
        v1 = v[0:i]
        v1 = v1.strip()
        v2 = v[i + 1 :]
        v2 = v2.strip()

        v3 = VarUtility.value_or_var_value(mdata=mdata, variables=variables, v=v2)
        if v3 is not None and isinstance(v3, str):
            v2 = v3.strip()
        elif v3 is not None:
            v2 = v3
        return (v1, v2)

    @classmethod
    def get_value(cls, mdata: dict, variables: dict, v: str):
        if v is None:
            return None
        v = mdata.get(v)
        if v is None:
            return None
        if isinstance(v, str):
            v = VarUtility.value_or_var_value(mdata=mdata, variables=variables, v=v)
        return v

    @classmethod
    def value_or_var_value(cls, *, mdata: dict, variables: dict, v: str):
        #
        # do any var swapping first. variable values are used like:
        #     var|name
        # this returns the value of the variable name. in reference form: $.variables.name
        #
        i = f"{v}".find("var|")
        if i > -1:
            v2 = f"{v}"[4:]
            v2 = v2.strip()
            if v2 in variables:
                v2 = variables[v2]
            v = v2
        #
        # do any meta swapping. metadata is the metadata from a csvpath's comments. e.g.
        #     description: this is my path
        # meta values are used like:
        #     meta|name
        # this returns the value of the metadata field name. in reference form: $.metadata.name
        #
        i = f"{v}".find("meta|")
        if i > -1 and mdata is not None:
            v2 = f"{v}"[5:]
            v2 = v2.strip()
            v2 = mdata.get(v2)
            v = v2
        #
        # if the value is ALL CAPS check if it is an
        # env var.
        if v and f"{v}".isupper():
            v2 = f"{v}".strip()
            v2 = os.getenv(v2)
            if v2 is not None:
                v = v2.strip()
        return v

    @classmethod
    def get_str(cls, mdata: dict, variables: dict, directive: str):
        v = VarUtility.get_value(mdata, variables, directive)
        v = f"{v}"
        v = v.strip()
        if v == "None":
            return None
        return v

    @classmethod
    def get_int(cls, mdata: dict, variables: dict, directive: str):
        v = VarUtility.get_value(mdata, variables, directive)
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
    def get_bool(cls, mdata: dict, variables: dict, directive: str) -> bool:
        v = VarUtility.get_value(mdata, variables, directive)
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
