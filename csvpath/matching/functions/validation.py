# pylint: disable=C0114
from typing import Type, List
from csvpath.matching.productions.matchable import Matchable
from ..util.exceptions import ChildrenException
from csvpath.util.config_exception import ConfigurationException


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
