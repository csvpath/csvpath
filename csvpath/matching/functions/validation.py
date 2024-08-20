from typing import Any, Type, List
from ..productions.matchable import Matchable
from ..util.exceptions import ChildrenException


class Validation(Matchable):
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

    def validate_zero_one_or_two_args(
        self, first_arg=[], second_arg=[], solo_arg=[]
    ) -> None:
        if len(self.children) == 0:
            pass
        elif len(self.children) == 1 and not hasattr(self.children[0], "op"):
            if not self._class_match(self.children[0], solo_arg):
                raise ChildrenException(f"{self.name}()'s argument must be {first_arg}")
        else:
            if not self._class_match(self.children[0].left, first_arg):
                raise ChildrenException(
                    f"{self.name}()'s first argument must be {first_arg}"
                )
            if not self._class_match(self.children[0].right, second_arg):
                raise ChildrenException(
                    f"{self.name}()'s second argument must be {second_arg}"
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

    def validate_one_arg(self, types=[]) -> None:
        if len(self.children) != 1:
            raise ChildrenException(f"{self.name}() must have 1 argument")
        if hasattr(self.children[0], "op") and self.children[0].op == ",":
            raise ChildrenException(
                f"{self}() must have 1 argument, not {self.children}, {self.children[0].op}"
            )
        if len(types) > 0:
            if not self._class_match(self.children[0], types):
                raise ChildrenException(
                    f"{self.name}() must have an argument of type: {types}"
                )

    def validate_one_or_more_args(self) -> None:
        if len(self.children) == 0:
            raise ChildrenException(f"{self.name}() must have 1 or more arguments")
        elif hasattr(self.children[0], "op") and self.children[0].op != ",":
            raise ChildrenException(f"{self.name}() must have 1 or more arguments")

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
        # must be an equality
        if len(self.children) != 1:
            raise ChildrenException(
                f"{self}() must have 2 or more arguments, not {len(self.children)}"
            )
        # , indicates arguments, at least 2
        elif not hasattr(self.children[0], "op"):
            raise ChildrenException(
                f"{self}() must have 2 or more arguments, not {self.children}"
            )
        elif self.children[0].op != ",":
            raise ChildrenException(
                f"{self.name}() must have 2 or more arguments, op: {self.children[0].op}"
            )
        # if we can't find left or right we have < 2 arguments. left or right
        # could be equalities so the number may be more than 2
        elif self.children[0].left is None or self.children[0].right is None:
            raise ChildrenException(f"{self.name}() must have 2 or more arguments")
