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
# separate integration question.
#
class Function3Describer:
    @classmethod
    def describe(
        cls, function_cls: type, name: "str | None" = None, markdown: bool = True
    ) -> str:
        """one function's own markdown documentation block. Heading is
        a plain "## {name}" (no backticks/colon/parens) specifically so
        describe_all()'s own index links resolve to a predictable
        "#{name}" anchor -- GitHub-flavored-markdown's own heading-to-
        anchor slugify rules are not consistent across renderers once
        punctuation is involved, so this sidesteps that entirely rather
        than trying to replicate one specific renderer's algorithm.

        `name` (added 2026-10-16, for the :before()/:after() alias
        rollout, compendium 6.28b) overrides the heading/inline-code
        text used throughout this block -- defaults to `function_cls.
        NAME`, unchanged for every direct caller that does not pass it.
        `describe_all()` passes each alias's own registered name
        explicitly, so an alias like ":below()" gets its own complete,
        correctly-anchored block rather than silently reusing/renaming
        ":before()"'s -- aliases are registered as extra dict keys
        pointing at the SAME class (see Before3's own docstring), so
        without this override every alias would describe itself as its
        canonical name, breaking describe_all()'s own "index and blocks
        agree on function count" invariant.

        `markdown` (added 2026-10-22 for the CLI function browser --
        see csvpath/cli/reference_function_lister.py) controls the
        table's own tablefmt, same "pipe"/"simple_grid" choice
        FunctionDescriber already makes for the identical CVL-side
        markdown-file-vs-terminal distinction: True (default, unchanged
        for every existing caller/test) renders a GFM pipe table for
        committed .md output; False renders a boxed simple_grid table,
        more readable printed directly to a terminal."""
        display_name = name if name is not None else function_cls.NAME
        lines = [f"## {display_name}", "", f"`:{display_name}()`", ""]
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
        kind = function_cls.metadata_kind()
        if kind:
            rows.append(["Resolves as", kind])
        if function_cls.SELECTOR_WHEN_ARGUED:
            rows.append(
                [
                    "Selector when argued",
                    "bare with an argument, selects the entity whose own "
                    "field matches it, rather than reading a field off an "
                    "already-selected one",
                ]
            )
        if markdown:
            lines.append(tabulate(rows, tablefmt="pipe"))
        else:
            # terminal-only wrapping -- some rows (e.g. "Selector when
            # argued"/"Positions") carry long free text that would
            # otherwise stretch simple_grid arbitrarily wide on a real
            # terminal; a GFM pipe table has no such concern (the
            # renderer wraps it), so this only applies here.
            lines.append(
                tabulate(rows, tablefmt="simple_grid", maxcolwidths=[22, 70])
            )
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
            lines.append(cls.describe(function_cls, name=name))
            lines.append("")
        return "\n".join(lines)
