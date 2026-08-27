from tabulate import tabulate

from .functions.reference_function_factory_3 import ReferenceFunctionFactory


#
# compendium 5.4: "Reference functions are self-documenting... must be
# able to output .md in a similar way to
# csvpath/cli/function_describer.py." Function3.describe() already
# gives the machine-readable half (a plain dict, meant for a future
# type-ahead layer's own registry query -- see its own docstring, kept
# unchanged here); this is the human-readable half, a separate
# describer paralleling FunctionDescriber's own shape rather than
# reusing it directly -- match-language functions have argsets/
# overloads/qualifiers that references-v3 functions simply do not (at
# most one arg, no overloads), so a from-scratch, much simpler renderer
# fits the actual Function3 model better than adapting the match-side
# one. Deliberately just a markdown-string producer -- writing the
# result to a file, or wiring it into any interactive CLI, is a
# separate integration question (v3 is not wired into production yet,
# see the bucket list).
#
class Function3Describer:
    @classmethod
    def describe(cls, function_cls: type) -> str:
        """one function's own markdown documentation block. Heading is
        a plain "## {name}" (no backticks/colon/parens) specifically so
        describe_all()'s own index links resolve to a predictable
        "#{name}" anchor -- GitHub-flavored-markdown's own heading-to-
        anchor slugify rules are not consistent across renderers once
        punctuation is involved, so this sidesteps that entirely rather
        than trying to replicate one specific renderer's algorithm."""
        lines = [f"## {function_cls.NAME}", "", f"`:{function_cls.NAME}()`", ""]
        if function_cls.SUMMARY:
            lines.append(function_cls.SUMMARY)
            lines.append("")
        rows = [["Role", function_cls.ROLE or "none"]]
        rows.append(
            [
                "Datatypes",
                ", ".join(function_cls.DATATYPES) if function_cls.DATATYPES else "none",
            ]
        )
        if function_cls.ARG_TYPES:
            type_names = ", ".join(t.__name__ for t in function_cls.ARG_TYPES)
            required = "required" if function_cls.ARG_REQUIRED else "optional"
            rows.append(["Argument", f"{type_names} ({required})"])
        else:
            rows.append(["Argument", "none"])
        if function_cls.POSITIONS:
            positions = "; ".join(
                f"{datatype}: {', '.join(pos) if pos else 'none'}"
                for datatype, pos in function_cls.POSITIONS.items()
            )
            rows.append(["Positions", positions])
        if function_cls.SOURCE:
            rows.append(["Source", function_cls.SOURCE])
        if function_cls.KEY:
            key = "; ".join(
                f"{datatype}: `{path}`" for datatype, path in function_cls.KEY.items()
            )
            rows.append(["Key", key])
        if function_cls.LEDGER_KEY:
            ledger_key = "; ".join(
                f"{datatype}: `{path}`"
                for datatype, path in function_cls.LEDGER_KEY.items()
            )
            rows.append(["Ledger fallback key", ledger_key])
        if function_cls.BARE_SOURCE:
            rows.append(["Bare source", function_cls.BARE_SOURCE])
        lines.append(tabulate(rows, tablefmt="pipe"))
        return "\n".join(lines)

    @classmethod
    def describe_all(cls) -> str:
        """the whole registry as one combined markdown document -- an
        alphabetical index (name + one-line summary) linking down to
        each function's own full block, mirroring FunctionDescriber.
        describe()'s own "[[Back to index]]" convention, just inverted
        (one document, not one page per function)."""
        names = sorted(ReferenceFunctionFactory.registered_names())
        lines = ["# References v3 Function Reference", "", "## Index", ""]
        for name in names:
            function_cls = ReferenceFunctionFactory.get_registered_class(name)
            summary = function_cls.SUMMARY or ""
            lines.append(f"- [`:{name}()`](#{name}) — {summary}")
        lines.append("")
        for name in names:
            function_cls = ReferenceFunctionFactory.get_registered_class(name)
            lines.append(cls.describe(function_cls))
            lines.append("")
        return "\n".join(lines)
