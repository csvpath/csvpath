# pylint: disable=C0114
from ..function_focus import MatchDecider
from csvpath.matching.productions import Term


class In(MatchDecider):
    """checks if the component value is in the values of the other N arguments.
    terms are treated as a delimited string of values"""

    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        siblings = self.children[0].commas_to_list()
        t = siblings[0].to_value(skip=skip)
        pln = self.matcher.csvpath.line_monitor.physical_line_number
        print(f"In._decide_match: pln: {pln}")
        inf = []
        for s in siblings[1:]:
            v = s.to_value(skip=skip)
            # print(f"In._decide_match: v: {v}")
            if isinstance(s, Term):
                vs = f"{v}".split("|")
                inf += vs
            else:
                if isinstance(v, list):
                    inf += v
                elif isinstance(v, dict):
                    for k in v:
                        inf.append(k)
                else:
                    inf.append(v)
        # print(f"In._decide_match: inf: {inf}, t: {t}")

        self.match = t in inf
