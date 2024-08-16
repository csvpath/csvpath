from typing import Any, Type, List
from csvpath.matching.productions.matchable import Matchable


class ChildrenException(Exception):
    pass


class Function(Matchable):
    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name)
        self.matcher = matcher
        self._function_or_equality = child
        if child:
            self.add_child(child)

    def __str__(self) -> str:
        return f"""{self._simple_class_name()}.{self.name}({self._function_or_equality if self._function_or_equality is not None else ""})"""

    # ------------ VALIDATION -------------

    def validate_zero_or_more_args(self, types=[]) -> None:
        if len(self.children) == 0:
            pass
        elif hasattr(self.children[0], "commas_to_list"):
            siblings = self.children[0].commas_to_list()
            if len(types) > 0:
                for _ in siblings:
                    if not self._class_match(_, types):
                        raise ChildrenException(
                            f"{self.name}() can only have these arguments: {types}"
                        )
        elif len(self.children) == 1:
            if len(types) > 0:
                if not self._class_match(self.children[0], types):
                    raise ChildrenException(
                        f"{self.name}() can only have these arguments: {types}"
                    )

    def validate_zero_args(self) -> None:
        if len(self.children) > 0:
            raise ChildrenException(f"{self.name}() cannot have arguments")

    def validate_zero_or_more_than_one_arg(self) -> None:
        if len(self.children) == 1 and not hasattr(self.children[0], "op"):
            raise ChildrenException(
                f"{self.name}() must have 0 or more than 1 argument"
            )
        elif len(self.children) == 0:
            pass
        elif (
            len(self.children) == 1
            and hasattr(self.children[0], "op")
            and self.children[0].op == ","
        ):
            pass
        else:
            raise ChildrenException(
                f"{self.name}() must have 0 or more than 1 argument"
            )

    def validate_zero_one_or_two_args(self, first_arg=[]) -> None:
        if len(self.children) == 0:
            pass
        elif len(self.children) == 1 and not hasattr(self.children[0], "op"):
            if not self._class_match(self.children[0], first_arg):
                raise ChildrenException(
                    f"{self.name}() must have its first argument in {first_arg}, not {self.children[0].__class__}"
                )
        else:
            if len(first_arg) and self.children[0].left.__class__ not in first_arg:
                raise ChildrenException(
                    f"{self.name}() must have its first argument in {first_arg}, not {self.children[0].__class__}"
                )

    def validate_zero_or_one_arg(self, types=[]) -> None:
        if len(self.children) > 1:
            raise ChildrenException(f"{self.name}() can only have 0 or 1 argument")
        elif len(self.children) == 0:
            pass
        elif hasattr(self.children[0], "op"):
            raise ChildrenException(f"{self.name}() can only have 0 or 1 argument")
        elif len(types) > 0:
            if not self._class_match(self.children[0], types):
                raise ChildrenException(
                    f"If {self.name}() has an argument it must be of type: {types}"
                )

    def validate_one_or_more_args(self) -> None:
        if len(self.children) == 0:
            raise ChildrenException(f"{self.name}() must have 1 or more arguments")
        elif hasattr(self.children[0], "op") and self.children[0].op != ",":
            raise ChildrenException(f"{self.name}() must have 1 or more arguments")

    def validate_one_arg(self, types=[]) -> None:
        if len(self.children) != 1:
            raise ChildrenException(f"{self.name}() must have 1 argument")
        elif hasattr(self.children[0], "op"):
            raise ChildrenException(f"{self.name}() must have 1 argument")
        if len(types) > 0:
            if not self._class_match(self.children[0], types):
                raise ChildrenException(
                    f"{self.name}() must have an argument of type: {types}"
                )

    def _class_match(self, obj, ok: List[Type]) -> bool:
        if not ok or len(ok) == 0:
            return True
        cls = obj.__class__
        if cls in ok:
            return True
        else:
            for _ in ok:
                if isinstance(obj, _):
                    return True
        return False

    def validate_one_or_two_args(self, one=[], left=[], right=[]) -> None:
        if len(self.children) != 1:
            raise ChildrenException(f"{self.name}() must have at least 1 argument")
        if hasattr(self.children[0], "op"):
            if self.children[0].op != ",":
                raise ChildrenException(
                    f"{self.name}() must have at least 1 argument and may have 2 arguments"
                )
            if len(left) > 0:
                if not self._class_match(self.children[0].left, left):
                    raise ChildrenException(
                        f"{self.name}()'s first argument must be of type: {left}, not {self.children[0].left.__class__}"
                    )
            if len(right) > 0:
                if not self._class_match(self.children[0].right, right):
                    raise ChildrenException(
                        f"{self.name}()'s second argument must be of type: {right}"
                    )
        else:
            if len(one) > 0:
                if not self._class_match(self.children[0], one):
                    raise ChildrenException(
                        f"{self.name}()'s argument must be of type: {one}"
                    )

    def validate_two_args(self, left=[], right=[]) -> None:
        """allows an equality of op '==' in left"""
        if len(self.children) != 1:
            raise ChildrenException(f"{self.name}() must have 2 arguments")
        elif not hasattr(self.children[0], "op"):
            raise ChildrenException(f"{self.name}() must have 2 arguments")
        if hasattr(self.children[0].left, "op") and self.children[0].left.op == ",":
            raise ChildrenException(f"{self.name}() can only have 2 arguments")
        if hasattr(self.children[0].right, "op"):
            raise ChildrenException(f"{self.name}() can only have 2 arguments")
        if len(left) > 0:
            if not self._class_match(self.children[0].left, left):
                raise ChildrenException(
                    f"{self.name}() must have a first argument of type: {left}"
                )
        if len(right) > 0:
            if not self._class_match(self.children[0].right, right):
                raise ChildrenException(
                    f"{self.name}() must have a second argument of type: {right}"
                )

    def validate_two_or_more_args(self) -> None:
        if len(self.children) != 1:
            raise ChildrenException(f"{self.name}() must have 2 or more arguments")
        elif not hasattr(self.children[0], "op"):
            raise ChildrenException(f"{self.name}() must have 2 or more arguments")
        elif self.children[0].op != ",":
            raise ChildrenException(f"{self.name}() must have 2 or more arguments")
        elif self.children[0].left is None or self.children[0].right is None:
            raise ChildrenException(f"{self.name}() must have 2 or more arguments")

    # ------------ OTHER STUFF -------------

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    def _noop_match(self) -> bool:
        return self.match if self.match is not None else True

    def _noop_value(self) -> bool:
        return self.value if self.value is not None else self._noop_match()

    def to_value(self, *, skip=[]) -> bool:
        #
        # in most cases, even trivial ones, a function overrides this method.
        #
        if self in skip:
            return True
        if self._function_or_equality:
            if not self._function_or_equality.matches(skip=skip):
                return False
        print(
            "WARNING: Function.to_value defaulting to True. You should override this method."
        )
        return True
