from dataclasses import dataclass, field

from .threshold_utility import ThresholdUtility as thut


@dataclass
class CsvPathParts:
    """the pieces of one generated csvpath, collected while converting a
    schema object, and rendered in a fixed order:

        metadata comment
        $[1*][            or $[*][ when there are first_checks
            first_checks  file-level checks that must also see a
                          header-only file (e.g. rowCount)
            first_line.nocontrib() -> skip()    only in the $[*] form
            line( line_args )
            line_checks   per-line checks outside the line()
            counters      threshold counters
            last_checks   threshold checks at the last line
        ]
    """

    metadata: dict[str, str] = field(default_factory=dict)
    first_checks: list[str] = field(default_factory=list)
    line_args: list[str] = field(default_factory=list)
    line_checks: list[str] = field(default_factory=list)
    counters: list[str] = field(default_factory=list)
    last_checks: list[str] = field(default_factory=list)

    INDENT = "    "

    @property
    def needs_full_scan(self) -> bool:
        #
        # with $[1*] a header-only file has no scanned line at all (see
        # issue #306), so checks that must see a header-only file need $[*]
        # and an explicit skip of the header line. threshold last_checks do
        # not: with no data lines there is nothing to count.
        #
        return bool(self.first_checks)

    def add_threshold(self, *, base: str, when: str, rule: dict) -> str:
        """adds a counter and its last-line check for a threshold rule, and
        returns the counter variable name.

        base: the variable name to use, made unique if another counter has
              it (two rules on one column, or column names that sanitize the
              same)
        when: the condition, with nocontrib, under which a line is counted

        counter() creates its variable at 0 on first evaluation, so no
        initialization is needed.
        """
        if not isinstance(base, str) or base.strip() == "":
            raise ValueError("base must be a non-empty str")
        if not isinstance(when, str) or when.strip() == "":
            raise ValueError("when must be a non-empty str")
        var = base
        n = 2
        while any(c.endswith(f"-> counter.{var}(1)") for c in self.counters):
            var = f"{base}_{n}"
            n += 1
        self.counters.append(f"{when} -> counter.{var}(1)")
        value = thut.count_value(var=var, rule=rule)
        fail_when = thut.fail_when(value=value, rule=rule)
        self.last_checks.append(
            f"and.nocontrib( {thut.LAST_DATA_LINE}, {fail_when} ) -> fail()"
        )
        return var

    def render(self) -> str:
        if len(self.line_args) == 0:
            raise ValueError("A csvpath needs at least one line() argument")
        i = self.INDENT
        out = ["~"]
        for k, v in self.metadata.items():
            out.append(f"  {k}: {v}")
        out.append("~")
        if self.needs_full_scan:
            out.append("$[*][")
            out.extend(f"{i}{c}" for c in self.first_checks)
            out.append(f"{i}first_line.nocontrib() -> skip()")
        else:
            out.append("$[1*][")
        out.append(f"{i}line(")
        out.append(",\n".join(f"{i}{i}{a}" for a in self.line_args))
        out.append(f"{i})")
        for checks in [self.line_checks, self.counters, self.last_checks]:
            out.extend(f"{i}{c}" for c in checks)
        out.append("]")
        return "\n".join(out) + "\n"
