# pylint: disable=C0114
from ..function_focus import MatchDecider
from csvpath.matching.productions import Header, Variable, Equality, Term
from csvpath.matching.util.exceptions import ChildrenException
from ..headers.headers import Headers
from csvpath.matching.util.expression_utility import ExpressionUtility


class Empty(MatchDecider):
    """checks for empty or blank header values in a given line.
    it reports True only if all the places it is directed to look are empty.
    if you pass it headers() it checks for all headers being empty."""

    def check_valid(self) -> None:
        if len(self.children) == 0:
            raise ChildrenException("empty() must have at least 1 argument")
        elif isinstance(self.children[0], Headers):
            if len(self.children) != 1:  # pragma: no cover
                raise ChildrenException(
                    "If empty() has a headers() argument it can only have 1 argument"
                )
        children = self.children
        if isinstance(self.children[0], Equality):
            children = self.children[0].commas_to_list()
        self._validate(children)
        super().check_valid()  # pragma: no cover

    def _validate(self, children):
        for s in children:
            if isinstance(s, Headers) and len(children) > 1:
                raise ChildrenException(
                    "If empty() has a headers() argument it can only have 1 argument"
                )
            if isinstance(s, Term):
                raise ChildrenException(
                    "empty() arguments cannot include terms"
                )  # pragma: no cover

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    #
    # empty(headers())
    # empty(#h, #h2, hn...)
    # empty(var=list)
    # empty(var=dict)
    # empty(var)
    # empty(ref)
    #
    def _decide_match(self, skip=None) -> None:
        print(f"empty._decide: chs: {self.children}")
        if len(self.children) == 1 and isinstance(self.children[0], Headers):
            self._do_headers(skip=skip)
        elif len(self.children) == 1 and isinstance(self.children[0], Equality):
            self._do_many(skip=skip)
        elif len(self.children) == 1:
            self._do_one(self.children[0], skip=skip)
        else:
            self._do_many(skip=skip)

    def _do_headers(self, skip=None):
        ret = True
        for i, h in enumerate(self.matcher.line):
            ret = self._is_empty(h)
            if ret is False:
                break
        self.match = ret

    def _do_many(self, skip=None):
        siblings = None
        if isinstance(self.children[0], Equality):
            siblings = self.children[0].commas_to_list()
        else:
            siblings = self.children[0]

        for s in siblings:
            print(f"empty._do_many: a sib: {s}")
            self._do_one(s)
            if self.match is False:
                break

    def _do_one(self, child, skip=None):
        v = child.to_value(skip=skip)
        self.match = self._is_empty(v)

    def _is_empty(self, v):
        ret = True
        if v is None:
            ret = True
        elif f"{v}".strip() == "":
            ret = True
        elif isinstance(v, list) or isinstance(v, tuple):
            for item in v:
                ret = self._is_empty(item)
                if not ret:
                    break
        elif isinstance(v, dict):
            ret = len(v) > 0
        else:
            ret = False
        return ret
