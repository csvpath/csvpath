"""
Prototype: grammar-driven autocomplete for CsvPath Reference Language v3,
using Lark's InteractiveParser instead of hand-maintained follow-set lists.

This replaces the mechanism in reference_transformer.py (manually writing
self.ref.next = [...] once per grammar production) with a query against the
parser's actual state. One source of truth (the grammar) instead of two.
"""
from lark import Lark, Token
from lark.exceptions import UnexpectedToken, UnexpectedCharacters

with open("reference_v3.lark") as f:
    GRAMMAR = f.read()

# LALR is required for parse_interactive -- confirmed available against v3's
# grammar (v3 is regular enough for LALR; v2's grammar required Earley
# because of its heavy ambiguous alternation, which is exactly why this
# technique wasn't available before).
parser = Lark(GRAMMAR, start="start", parser="lalr")


def next_terminals(partial_text: str):
    """
    Given a partial (possibly incomplete/invalid-as-a-whole) reference
    string, return the set of terminal names that would be legal as the
    very next token, derived from actual parser state -- not a hand-written
    list.
    """
    interactive = parser.parse_interactive(partial_text)
    try:
        interactive.exhaust_lexer()
    except (UnexpectedToken, UnexpectedCharacters):
        pass
    choices = interactive.choices()
    # Filter out non-terminal/internal entries (rule names, $END) -- a
    # context menu only cares about things the user could actually type.
    terminal_names = {
        name for name in choices
        if name.isupper() and name not in ("$END",)
    }
    return terminal_names, choices


def describe(name: str) -> str:
    """Human-readable label for a terminal name, for menu display."""
    labels = {
        "DOLLAR": "$  (start a reference)",
        "DOT": ".  (next slot)",
        "COLON": ":  (start a function)",
        "STAR": "*  (all named-files/paths/results)",
        "LPAR": "(",
        "RPAR": ")",
        "SLASH": "/",
        "HASH": "#  (minor name)",
        "IDENTIFIER": "<identifier>",
        "LITERAL": "<text>",
        "STRING": '"<text>"',
        "VARIABLE": "@<variable>",
        "SIGNED_NUM": "<number>",
    }
    return labels.get(name, name)


def current_slot(partial_text: str) -> str:
    """
    Which of the four slots ($, root_major / datatype / name_one / name_three)
    the cursor is currently positioned in, based on dot-count in the text
    typed so far. This counts top-level dots only -- naive about dots that
    might appear inside a quoted string argument, which a real
    implementation should guard against (not needed to prove the mechanism
    here, but flagged rather than silently wrong).
    """
    # strip $ and split on "." -- crude but sufficient for the prototype
    body = partial_text.lstrip("$")
    dot_count = body.count(".")
    if dot_count == 0:
        return "root_major"
    elif dot_count == 1:
        return "datatype"
    elif dot_count == 2:
        return "name_one"  # path slot
    else:
        return "name_three"  # part slot


def current_datatype(partial_text: str) -> str:
    for dt in ("files", "csvpaths", "results"):
        if f".{dt}." in partial_text or partial_text.endswith(f".{dt}"):
            return dt
    return None


def suggest(partial_text: str, registry: dict = None):
    """
    Two-layer suggestion:
      1. Grammar layer (parser state) answers "what shape comes next"
         (a function, a literal, a slash, end-of-slot, etc.)
      2. Registry layer answers "which named options," filtered by BOTH
         datatype and slot (path vs part) -- both derived from the text
         typed so far via simple, robust rules (dot-counting, substring
         match), not from raw parser state internals (which are an
         implementation detail of the LALR tables and shouldn't be
         pattern-matched against directly -- that would just recreate the
         original hand-coupling problem one layer down).
    """
    terminals, _ = next_terminals(partial_text)
    slot = current_slot(partial_text)
    datatype = current_datatype(partial_text)
    suggestions = []

    for t in sorted(terminals):
        if t == "COLON" and registry:
            for name, fn in registry.items():
                dt_ok = datatype is None or datatype in fn.get("datatypes", ())
                slot_ok = slot in fn.get("slots", ("name_one", "name_three"))
                if dt_ok and slot_ok:
                    suggestions.append(f":{name}(...)  -- {fn['summary']}")
        else:
            suggestions.append(describe(t))

    return suggestions


if __name__ == "__main__":
    # minimal stand-in registry, shaped like function_registry_prototype.py's
    # to_tool_description() output -- in the real implementation this would
    # BE that registry, not a duplicate of it
    mini_registry = {
        "name": {"summary": "Filter by name/identity at this position.",
                  "datatypes": ("files", "csvpaths", "results"),
                  "slots": ("name_one", "name_three")},
        "all": {"summary": "Every version of the surviving identity.",
                 "datatypes": ("files", "csvpaths", "results"),
                 "slots": ("name_one", "name_three")},
        "last": {"summary": "Most recent version (reducer).",
                  "datatypes": ("files", "csvpaths", "results"),
                  "slots": ("name_one", "name_three")},
        "errors": {"summary": "The run's errors.json.",
                    "datatypes": ("results",),
                    "slots": ("name_three",)},  # part slot ONLY -- not a path-slot concept
        "vars": {"summary": "The run's vars.json.",
                  "datatypes": ("results",),
                  "slots": ("name_three",)},
    }

    print("\n--- layer 1 only (grammar/terminal names) ---")
    test_cases = [
        "",
        "$",
        "$*",
        "$*.",
        "$*.files",
        "$*.files.",
        "$*.files.:name(",
        '$*.files.:name("Acme")',
        '$*.files.:name("Acme").',
    ]
    for case in test_cases:
        terminals, raw_choices = next_terminals(case)
        readable = sorted(describe(t) for t in terminals)
        print(f"after {case!r:35} -> {readable}")

    print("\n--- layer 2 (grammar + registry, datatype AND slot filtered) ---")
    layered_cases = [
        "$*.files.",                  # name_one (path) slot, files -- expect name/all/last, NOT errors/vars
        "$*.results.",                # name_one (path) slot, results -- same ordinal vocab, still no errors/vars
        '$*.results.:last().',        # name_three (part) slot, results -- NOW expect errors/vars too
    ]
    for case in layered_cases:
        print(f"\nafter {case!r}  [slot={current_slot(case)}, datatype={current_datatype(case)}]:")
        for s in suggest(case, mini_registry):
            print(f"   {s}")
