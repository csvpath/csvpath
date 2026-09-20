from lark import Lark, Tree, UnexpectedInput


#
# references v3 are AI-facing query strings over CsvPath Framework's
# named-file, named-paths, and named-results storage. The controlling spec
# is `specs/references_v3/spec/references_v3_compendium.md`, together with
# its normative examples (`normative_reference_examples.txt`) and the
# manifest field-accessor reference
# (`references_v3_required_manifest_functions.md`). Those three documents
# are the source of truth for what this grammar must accept and what any
# given reference means. This file's own comments are scoped to
# grammar/parser-level decisions -- why a production is shaped the way it
# is -- not to restating reference-language semantics; semantics belong in
# the compendium and drift silently out of sync if duplicated here.
# (`specs/references_v3/notes/creating references v3.txt` is an early,
# superseded design note, not the spec -- kept only as dev history, per
# the compendium's own listing of that directory as non-normative.)
#
# a reference has the shape:
#   $root_major.datatype.name_one[.name_three]
# where name_one may itself carry a "#name_two" (an XLSX worksheet name,
# files datatype only).
#
# grammar-level design notes worth keeping in mind when reading this file:
#
# - name_three's required-ness differs by datatype -- see the compendium
#   for which datatypes require it and what its absence means; not
#   restated here since that's semantics, not grammar. Rather than
#   tripling the reference rule per datatype, name_three is kept
#   grammatically optional everywhere and its required-ness is enforced
#   later as a semantic check (in the transformer/finder, not yet built)
#   against the already-parsed datatype. this keeps the grammar itself flat
#   and is the main way v3 avoids the combinatorial rule explosion of the
#   v1/v2 grammar (reference_grammar.py's files_names alone has ~25
#   alternatives).
#
# - "*" and a bare ":all()" function are grammatically similar (both legal
#   at a path-segment position) but semantically distinct -- see the
#   compendium (§3.8, §4) for what each means and how grouping scopes; not
#   restated here since that's semantics, not grammar. The grammar treats
#   "*" and ":all()" as distinct tokens/productions either way; the actual
#   flatten-vs-group reading is a semantic interpretation enforced by the
#   transformer, not a grammar-level concern.
#
# - name_one is: a "/"-joined path (segments are a literal name, "*", or a
#   single function occupying the whole segment), optionally followed by a
#   "#name_two" worksheet marker, optionally followed by a function chain
#   (functions ANDed together with no separator between them). there is no
#   separate "bare function chain" alternative: a name_one with no literal/
#   wildcard path at all (e.g. ":all()", ":before(:yesterday()):index(3)")
#   is produced by path_prefix reducing to a single function-segment,
#   followed by the rest of the functions as the trailing func_chain. an
#   earlier version of this grammar had `name_one: path_prefix (...)
#   func_chain? | func_chain` as two alternatives, but the second was
#   redundant with the first (any string it could produce, the first
#   branch already produces via its single-function-segment case) *and* it
#   made the grammar genuinely ambiguous -- Earley silently picked one of
#   two valid parse trees for any bare function chain, and the ambiguity
#   also blocked LALR (a reduce/reduce collision on COLON, since the
#   parser couldn't decide with one token of lookahead whether an upcoming
#   function was "the sole path segment" or "the start of the bare
#   func_chain" branch). removing the redundant alternative fixed both:
#   one parse tree per string, and LALR compiles/parses cleanly (confirmed
#   against the full positive/negative test corpus before switching
#   QueryParser3 over). name_three has no equivalent issue -- its literal/
#   wildcard body can't itself be a function, so there's no analogous
#   ambiguity to remove there.
#
# - name_three is: an optional single body (a literal name or "*", no path
#   building -- "name_three cannot have free-standing forward slashes" per
#   spec), optionally followed by a function chain -- or just a bare
#   function chain.
#
# - function arguments accept a quoted string, a signed int, an "@name"
#   runtime-bound variable, a nested function call, or a slash-delimited
#   regex literal (REGEX, e.g. :name(/^(?:Mon|Tue)day$/) -- mirrors the
#   REGEX/REGEX_INNER convention already used by the match-language
#   grammar in csvpath/matching/lark_parser.py). there is deliberately no
#   bare/unquoted catch-all argument token: every regex argument, grouped
#   or not, goes through REGEX, so there is exactly one way to write one.
#   A bare "*" is NOT a legal argument (removed 2026-09-20 -- no
#   documented use case anywhere in the spec corpus; STAR remains legal
#   at root_major/name_one/name_three positions, just not as a function
#   argument).
#
# - root_major also accepts a function (added 2026-08-27, for :regex()) --
#   NOT a bare REGEX token directly at this position. This mirrors the
#   grammar's existing invariant that REGEX only ever appears inside
#   `arg` (an argument value), never occupying a whole grammatical slot
#   on its own -- a bare "/pattern/" as root_major would be the one
#   place that broke that rule. The grammar stays permissive here (any
#   function, not specifically :regex()) the same way it already is
#   everywhere else in this file -- which specific function names are
#   legal at which position is a semantic check the finder/Reference3
#   makes, not a grammar-level restriction (see e.g. name_one's own
#   function-valued segments, validated by each finder's own recognized-
#   shape checks, not baked into the grammar as separate productions per
#   function name).
#
REFERENCE_GRAMMAR_3 = r"""
    ?start: reference

    reference: "$" root_major "." datatype "." name_one ("." name_three)?

    root_major: STAR
              | IDENTIFIER
              | function

    datatype: FILES
            | CSVPATHS
            | RESULTS

    FILES: "files"
    CSVPATHS: "csvpaths"
    RESULTS: "results"

    //========================================
    // name_one: "/"-joined path, optional #worksheet (files only, but not
    // restricted here -- see module docstring), optional trailing function
    // chain. a path-less, function(s)-only name_one (e.g. ":all()") is
    // produced by path_prefix reducing to a single function-segment --
    // see module docstring for why there is no separate bare-func_chain
    // alternative here (there was; it was redundant and ambiguous).

    name_one: path_prefix ("#" name_two)? func_chain?

    path_prefix: segment ("/" segment)*
    segment: STAR
           | PATH_SEGMENT
           | function

    name_two: IDENTIFIER

    //========================================
    // name_three: optional single body (no path building), optional
    // trailing function chain. or a bare function chain.

    name_three: (PATH_SEGMENT | STAR) func_chain?
              | func_chain

    //========================================
    // functions: colon-prefixed, 0 or 1 arg, chainable with no separator
    // between them (functions are ANDed together per spec).

    func_chain: function+
    function: ":" FNAME "(" arg? ")"

    arg: STRING
       | SIGNED_INT
       | AT_VAR
       | function
       | REGEX

    //========================================
    // terminals

    STAR: "*"
    AT_VAR: "@" IDENTIFIER
    FNAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_\-]*/
    PATH_SEGMENT: /[a-zA-Z0-9_\-]+/
    //
    // STRING is deliberately opaque: "{...}" interpolation (compendium
    // §6.42 -- @variable and VALUE-role function-call spans, "{{"/"}}"
    // escaping) is NOT parsed here. This is an open implementation
    // choice, not a settled requirement either way -- interpolated
    // strings aren't expected to get complex, so validating "{...}"
    // structure as a post-parse/transform-time step (walking the
    // resolved string) is a reasonable default, but tightening this
    // grammar to parse "{...}" structure directly (a STRING production
    // built from literal-text and interpolation-span alternatives)
    // would be equally acceptable if that turns out easier to get right.
    // Whoever builds the transformer should pick one, not assume this
    // comment has already decided it.
    //
    STRING: /"(?:[^"\\]|\\.)*"/
    SIGNED_INT: /-?\d+/
    //
    // slash-delimited regex literal -- the one way to write a regex
    // argument, grouped or not. matches the REGEX/REGEX_INNER convention
    // already established in csvpath/matching/lark_parser.py.
    //
    REGEX: "/" REGEX_INNER "/"
    REGEX_INNER: /([^\/\\]|\\.)*/

    %import common.WS
    %ignore WS
"""


class QueryParser3:
    #
    # syntax-only parser for references v3. builds and validates the parse
    # tree; does not (yet) transform it into a ReferenceParser3 object
    # graph or enforce datatype-specific semantic rules (e.g. name_three
    # being required for files/csvpaths) -- that is deferred to the
    # transformer, not yet built. see module docstring.
    #
    # lalr, not earley: the grammar is unambiguous (see module docstring's
    # note on the removed bare-func_chain alternative), so lalr is
    # available and is what a later type-ahead layer will need -- lalr
    # parsing is deterministic one state at a time, which is what makes
    # Lark's parse_interactive()/InteractiveParser.choices() able to
    # answer "what's legal next" from actual parser state. earley has no
    # equivalent single-state mechanism.
    #
    def __init__(self) -> None:
        self.parser = Lark(REFERENCE_GRAMMAR_3, parser="lalr")

    def parse(self, query: str) -> Tree:
        if not query:
            raise ValueError("Query cannot be None or empty")
        return self.parser.parse(query)

    def validate_query(self, query: str) -> bool:
        try:
            self.parse(query)
            return True
        except UnexpectedInput:
            return False
