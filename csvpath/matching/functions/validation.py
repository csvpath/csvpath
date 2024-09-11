# pylint: disable=C0114
from typing import Type, List

# from csvpath.matching.productions.equality import Equality
from csvpath.matching.productions.matchable import Matchable
from ..util.exceptions import ChildrenException


class Validation(Matchable):
    """validations on the number of child match component productions expected
    and their types. there are no value tests and cannot be until all the
    structural tests (these) are completed."""

    def _class_match(self, obj, ok: List[Type]) -> bool:
        if not ok or len(ok) == 0:
            return True
        cls = obj.__class__
        if cls in ok:
            return True
        for _ in ok:
            if isinstance(obj, _):
                return True
        return False  # pragma: no cover

    def validate_zero_args(self) -> None:  # pylint: disable=C0116
        if len(self.children) > 0:
            raise ChildrenException(
                f"{self.name}() cannot have arguments"
            )  # pragma: no cover

    def validate_zero_or_one_arg(self, types=None) -> None:  # pylint: disable=C0116
        if types is None:
            types = []
        if len(self.children) > 1:
            raise ChildrenException(
                f"{self.name}() can only have 0 or 1 argument"
            )  # pragma: no cover
        if len(self.children) == 0:
            pass
        elif hasattr(self.children[0], "op"):
            raise ChildrenException(f"{self.name}() can only have 0 or 1 argument")
        elif len(types) > 0:
            if not self._class_match(self.children[0], types):
                raise ChildrenException(  # pragma: no cover
                    f"If {self.name}() has an argument it must be of type: {types}"
                )

    def validate_zero_or_more_than_one_arg(
        self,
    ) -> None:  # pragma: no cover  pylint: disable=C0116
        # TODO: if not used remove this method
        if len(self.children) == 1 and not hasattr(self.children[0], "op"):
            raise ChildrenException(
                f"{self.name}() must have 0 or more than 1 argument"
            )
        if len(self.children) == 0:
            pass
        elif (
            len(self.children) == 1
            and hasattr(self.children[0], "op")
            and self.children[0].op == ","
        ):
            pass  # pragma: no cover
        else:
            raise ChildrenException(
                f"{self.name}() must have 0 or more than 1 argument"
            )

    def validate_zero_or_more_args(self, types=None) -> None:  # pylint: disable=C0116
        if types is None:
            types = []
        if len(self.children) == 0:
            pass
        elif (
            len(self.children) == 1
            and hasattr(self.children[0], "commas_to_list")
            and self.children[0].op == ","
        ):
            siblings = self.children[0].commas_to_list()
            if len(types) > 0:
                for _ in siblings:
                    if not self._class_match(_, types):
                        raise ChildrenException(
                            f"{self.name}() can only have these arguments: {types}, not {_}"
                        )
        elif len(self.children) == 1:
            if len(types) > 0:
                if not self._class_match(self.children[0], types):
                    raise ChildrenException(
                        f"{self.name}() can only have these arguments: {types}"
                    )
        else:
            raise ChildrenException(
                f"{self.name}() must have one child, optionally with children of type: {types}"
            )

    def validate_zero_one_or_two_args(  # pylint: disable=C0116
        self, *, first_arg=None, second_arg=None, solo_arg=None
    ) -> None:
        if len(self.children) == 0:
            pass
        elif len(self.children) == 1 and not hasattr(self.children[0], "op"):
            if not self._class_match(self.children[0], solo_arg):
                raise ChildrenException(f"{self.name}()'s argument must be {first_arg}")
        else:
            if not self.children[0].op == ",":
                raise ChildrenException(f"{self.name} children opperation is incorrect")
            if not self._class_match(self.children[0].left, first_arg):
                raise ChildrenException(
                    f"{self.name}()'s first argument must be {first_arg}"
                )
            if not self._class_match(self.children[0].right, second_arg):
                raise ChildrenException(
                    f"{self.name}()'s second argument must be {second_arg}"
                )

    def validate_one_arg(self, types=None) -> None:  # pylint: disable=C0116
        if types is None:
            types = []
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

    def validate_one_or_more_args(self) -> None:  # pylint: disable=C0116
        if len(self.children) == 0:
            raise ChildrenException(f"{self.name}() must have 1 or more arguments")
        if hasattr(self.children[0], "op") and self.children[0].op != ",":
            raise ChildrenException(f"{self.name}() must have 1 or more arguments")

    def validate_one_or_two_args(  # pylint: disable=C0116
        self, one=None, left=None, right=None
    ) -> None:
        if len(self.children) != 1:
            raise ChildrenException(f"{self.name}() must have at least 1 argument")
        if hasattr(self.children[0], "op"):
            if self.children[0].op != ",":
                raise ChildrenException(
                    f"{self.name}() must have at least 1 argument and may have 2 arguments"
                )
            if left and len(left) > 0:
                if not self._class_match(self.children[0].left, left):
                    t = type(self.children[0].left)
                    raise ChildrenException(
                        f"{self.name}()'s first arg must be {left}, not {t}"
                    )
            if right and len(right) > 0:
                if not self._class_match(self.children[0].right, right):
                    raise ChildrenException(
                        f"{self.name}()'s second argument must be of type: {right}"
                    )
        else:
            if one and len(one) > 0:
                if not self._class_match(self.children[0], one):
                    raise ChildrenException(
                        f"{self.name}()'s argument must be of type: {one}"
                    )

    def validate_two_args(self, left=None, right=None) -> None:  # pylint: disable=C0116
        """allows an equality of op '==' in left"""
        if left is None:
            left = []
        if right is None:
            right = []
        if len(self.children) != 1:
            raise ChildrenException(f"{self.name}() must have 2 arguments")
        if not hasattr(self.children[0], "op"):
            raise ChildrenException(f"{self.name}() must have 2 arguments")
        if not self.children[0].op == ",":
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

    def validate_two_or_three_args(self) -> None:  # pylint: disable=C0116
        cs = self.children
        if cs is None:
            raise ChildrenException(
                f"{self.name}() must have two or three args, not none"
            )
        if len(cs) == 0:
            raise ChildrenException(f"{self.name}() must have two or three args, not 0")
        if not hasattr(cs[0], "op"):
            raise ChildrenException(f"{self.name}() must have two or three args, not 0")
        if cs[0].op != ",":
            raise ChildrenException(f"{self.name}() must have two or three args, not 0")
        if len(cs) == 1 and hasattr(cs[0], "op"):
            child = cs[0]
            if child.left is None or child.right is None:
                raise ChildrenException(
                    f"{self.name}() must have two or three args, not 1: {child}"
                )
            if child.op != ",":
                raise ChildrenException(
                    f"{self.name}() must have two or three args, not: {child}"
                )
        elif len(cs) > 3:
            raise ChildrenException(
                f"{self.name}() must have two or three args, not: {cs}"
            )

    def validate_two_or_more_args(
        self,
        one_when_two=None,
        one_when_more=None,
        two_when_two=None,
        two_when_more=None,
    ) -> None:  # pylint: disable=C0116
        # must be an equality
        if len(self.children) != 1:
            raise ChildrenException(
                f"{self}() must have 2 or more arguments, not {len(self.children)}"
            )
        # indicates arguments, at least 2
        if not hasattr(self.children[0], "op"):
            raise ChildrenException(
                f"{self}() must have 2 or more arguments, not {self.children}"
            )
        if self.children[0].op != ",":
            raise ChildrenException(
                f"{self.name}() must have 2 or more arguments, op: {self.children[0].op}"
            )
        # if we can't find left or right we have < 2 arguments. left or right
        # could be equalities so the number may be more than 2
        if self.children[0].left is None or self.children[0].right is None:
            raise ChildrenException(f"{self.name}() must have 2 or more arguments")

        if (
            one_when_two
            and two_when_two
            and not hasattr(self.children[0].children[0], "op")
            and not hasattr(self.children[0].children[1], "op")
        ):
            if not self._class_match(self.children[0].left, one_when_two):
                raise ChildrenException(
                    f"""{self.name}() must have 2 or more arguments.
                    when there are 2 arguments the 1st must be in %s.", one_when_two
                    """
                )
            if not self._class_match(self.children[0].right, two_when_two):
                raise ChildrenException(
                    f"""{self.name}() must have 2 or more arguments.
                    when there are 2 arguments the 2st must be in %s.", two_when_two
                    """
                )
        elif one_when_more and two_when_more:
            if not self._class_match(self.children[0].left, one_when_more):
                raise ChildrenException(
                    f"""{self.name}() must have 2 or more arguments.
                    when there are more than 2 arguments
                    the 1st must be in %s.", one_when_more
                    """
                )
            if not self._class_match(self.children[0].right, two_when_more):
                raise ChildrenException(
                    f"""{self.name}() must have 2 or more arguments.
                    when there are more than 2 arguments
                    the 2st must be in %s.", two_when_more
                    """
                )

    def validate_three_args(self) -> None:  # pylint: disable=C0116
        cs = self.children
        if cs is None:
            raise ChildrenException(f"{self.name}() must have three args, not none")
        if len(cs) == 1 and hasattr(cs[0], "op"):
            child = cs[0]
            if len(child.children) != 3:
                raise ChildrenException(f"{self.name}() must have three args")
        elif len(cs) != 3:
            raise ChildrenException(f"{self.name}() must have three args")
