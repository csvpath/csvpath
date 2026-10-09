from dataclasses import dataclass, field


@dataclass
class CsvPathParts:
    """the pieces of one generated csvpath, collected while converting a
    schema object, and rendered in a fixed order:

        metadata comment
        $[1*][            or $[*][ when there are file-level checks
            first_checks  file-level checks that must also see a
                          header-only file (e.g. rowCount)
            inits         threshold counter initializations
            first_line.nocontrib() -> skip()
            line( line_args )
            line_checks   per-line checks outside the line()
            counters      threshold counters
            last_checks   threshold checks at the last line
        ]
    """

    metadata: dict[str, str] = field(default_factory=dict)
    first_checks: list[str] = field(default_factory=list)
    inits: list[str] = field(default_factory=list)
    line_args: list[str] = field(default_factory=list)
    line_checks: list[str] = field(default_factory=list)
    counters: list[str] = field(default_factory=list)
    last_checks: list[str] = field(default_factory=list)

    INDENT = "    "

    @property
    def needs_full_scan(self) -> bool:
        #
        # with $[1*] a header-only file never reaches last(), so file-level
        # checks need $[*] and an explicit skip of the header line
        #
        return bool(self.first_checks or self.inits or self.last_checks)

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
            out.extend(f"{i}{c}" for c in self.inits)
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
