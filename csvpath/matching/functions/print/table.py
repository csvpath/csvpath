# pylint: disable=C0114
import textwrap
from tabulate import tabulate
from ..function_focus import SideEffect


class HeaderTable(SideEffect):
    """prints a header table"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        table = []
        headers = ["#N", "#Name"]
        for i, h in enumerate(self.matcher.csvpath.headers):
            table.append([i, h])
        self.matcher.csvpath.print(
            tabulate(table, headers=headers, tablefmt="simple_grid")
        )
        self.match = self.default_match()


class RowTable(SideEffect):
    """prints a row table"""

    def check_valid(self) -> None:
        self.validate_zero_one_or_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        v1 = self._value_one()
        v2 = self._value_two()
        i = -1
        j = -1
        if v1 is None and v2 is None:
            i = 0
            j = len(self.matcher.csvpath.headers)
        elif v2 is None:
            i = v1
            j = i
        else:
            i = v1
            j = v2
        headers = []
        row = None
        print(f"tables.i: {i}, {j}")
        if i == j:
            headers.append(self.matcher.csvpath.headers[i])
            row = [[self.matcher.line[i]]]
        else:
            for k, h in enumerate(self.matcher.csvpath.headers[i : j + 1]):
                headers.append(f"#{h} (#{k + i})")
            row = [self.matcher.line[i : j + 1]]

        self.matcher.csvpath.print(
            tabulate(row, headers=headers, tablefmt="simple_grid")
        )
        self.match = self.default_match()


class VarTable(SideEffect):
    """prints a variables table"""

    def check_valid(self) -> None:
        self.validate_zero_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        v1 = self._value_one()
        v2 = self._value_two()
        if v1 is None:
            self.print_all_vars()
        elif v2 is None:
            self.print_one_var()
        else:
            self.print_some_vars(skip)
        self.match = self.default_match()

    def print_all_vars(self):
        headers = []
        rows = [[]]
        for k, v in self.matcher.csvpath.variables.items():
            headers.append(k)
            v = str(v)
            if len(v) > 20:
                v = textwrap.fill(v, width=20)
            rows[0].append(v)
        self.matcher.csvpath.print(
            tabulate(rows, headers=headers, tablefmt="simple_grid")
        )

    def print_one_var(self):
        h = self._value_one()
        headers = [h]
        rows = []
        v = self.matcher.csvpath.variables[h]
        if isinstance(v, list):
            for a in v:
                rows.append([a])
        elif isinstance(v, dict):
            headers.append("Tracking")
            for k, _ in v.items():
                rows.append([k, _])
        self.matcher.csvpath.print(
            tabulate(rows, headers=headers, tablefmt="simple_grid")
        )

    def print_some_vars(self, skip):
        siblings = self[0].commas_to_list()
        headers = []
        for s in siblings:
            headers.append(s.to_value(skip=skip))
        rows = []
        for h in headers:
            v = self.matcher.csvpath.variables[h]
            v = f"{v}"
            if len(v) > 30:
                v = textwrap.fill(v, width=30)
            rows.append([v])
        self.matcher.csvpath.print(
            tabulate(rows, headers=headers, tablefmt="simple_grid")
        )
