from typing import Any
from .function import Function, ChildrenException
from math import sqrt


class Correlate(Function):
    def _float(self, v: Any) -> float:
        try:
            return float(v)
        except Exception:
            return None

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException("Correlate function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(
                f"Correlate function must have an equality with the ',' operation, not {self.children[0].op}"
            )
        if self.value is None:
            om = self.has_onmatch()
            if not om or self.line_matches():
                child = self.children[0]
                left = child.left
                right = child.right
                leftv = left.to_value()
                rightv = right.to_value()

                lv = self._float(leftv)
                rv = self._float(rightv)

                name = self.first_non_term_qualifier("correlate")
                if lv is None or rv is None:
                    #
                    # variables[name][lineno]=(left,right)
                    self.matcher.set_variable(
                        f"{name}_gap",
                        value=(lv, rv),
                        tracking=self.matcher.csvpath.line_number,
                    )
                else:
                    nl = f"{name}_left"
                    nr = f"{name}_right"
                    leftlist = self.matcher.get_variable(nl)
                    rightlist = self.matcher.get_variable(nr)

                    if leftlist is None:
                        leftlist = []
                    leftlist.append(lv)

                    if rightlist is None:
                        rightlist = []
                    rightlist.append(rv)

                    self.matcher.set_variable(nl, value=leftlist)
                    self.matcher.set_variable(nr, value=rightlist)

                    if len(leftlist) == 1:
                        #
                        # not a lot to go on. skip the rest.
                        return self.value
                    elif len(leftlist) != len(rightlist):
                        #
                        # how could this happen?
                        raise Exception(
                            "Number of values to calculate correlation from must be the same"
                        )

                    mean_left = sum(leftlist) / len(leftlist)
                    mean_right = sum(rightlist) / len(rightlist)

                    var_left = sum((li - mean_left) ** 2 for li in leftlist)
                    var_right = sum((ri - mean_right) ** 2 for ri in rightlist)

                    if var_left == 0 or var_right == 0:
                        #
                        # how do we want to handle this? how likely is it?
                        print(f"skipping because 0: {var_left}, {var_right}")
                        return None

                    cov_lr = sum(
                        (li - mean_left) * (ri - mean_right)
                        for li, ri in zip(leftlist, rightlist)
                    )
                    cor = cov_lr / (sqrt(var_left) * sqrt(var_right))
                    #
                    # store:
                    #   - line number
                    #   - variance left
                    #   - variance right
                    #   - covariance
                    #   - correlation
                    #
                    vs = (
                        self.matcher.csvpath.line_number,
                        var_left,
                        var_right,
                        cov_lr,
                        cor,
                    )

                    self.matcher.set_variable(name, value=vs)

                    self.value = cor

        return self.value

    def matches(self, *, skip=[]) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()
