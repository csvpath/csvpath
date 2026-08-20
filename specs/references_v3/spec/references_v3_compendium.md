# CsvPath References v3 — Compendium

A standalone definition of the References v3 subsystem, synthesized directly
from the persisted spec, requirements notes, example queries, and the actual
implementation and test code as of 2026-07-31. This document does not
reconstruct any chat history — where a design point was worked out through
back-and-forth, only the resulting, settled fact is stated here.

Sources read to produce this document: `references_notes/creating references
v3.txt` (the frozen/current spec, most recently revised by David), `references_
notes/requirements for functions.txt`, `references_notes/more_reference_
queries.txt`, `references_notes/autocomplete_prototype.py`, all of `csvpath/
references/` (grammar, transformer, object graph, parser, exceptions, finder
ABC, results container, functions subpackage, the one concrete finder), all of
`tests/references/`, and this project's own persisted design-memory files.

---

## 1. What this is and why

CsvPath Framework stores data under three kinds of named things: **named-files**
(registered input files, each with multiple content versions identified by
SHA256-hash filename), **named-paths groups** (registered sets of CsvPath
statements, versioned as entries in a manifest array rather than as separate
files), and **named-results** (the output of running a named-paths group
against a named-file — a run directory containing one subdirectory per
statement in the group, each with its own result files: `data.csv`,
`errors.json`, `vars.json`, `meta.json`, etc.).

CsvPath already has two prior reference languages:

- **v1** set the current `$`-prefixed path/name syntax users see everywhere
  (e.g. `$myfile.files.abc`).
- **v2** updated the parsing/resolving implementation behind that same
  syntax (`csvpath/util/references/`: `ReferenceParser`, `FilesReferenceFinder2`,
  `ResultsReferenceFinder2`, `reference_transformer.py`, etc., ~2500 lines).
  v2's grammar/transformer hard-codes every operator combination per datatype
  (one rule alone has ~25 alternatives) — a "detuned," heavily combinatorial
  design that David has confirmed was deliberately shaped that way in an
  attempt at type-ahead support he didn't know how to do properly at the time.

**v3 is a from-scratch replacement**, motivated by two things: v1/v2 have
real tech debt and lack conceptual clarity, and — the main driver — a more
robust reference language can give an AI assistant a single, concise,
general-purpose exploration tool for digging into CsvPath project state,
instead of requiring many narrow, brittle, purpose-built tools.

v3 is **AI-facing only, for now**. v1/v2 stay exactly where they are, untouched,
and remain what end users see (identifying runs, registrations, named-paths
loads). v3 lives in a new location — `csvpath/references/` (top-level, not
under `util/`) — and follows v1/v2's own naming convention: `_3.py` files,
`3`-suffixed class names (`ReferenceParser3`, not `ReferenceParserV3`). Tests
live in `tests/references/`.

v3 covers only named-file, named-paths-group, and named-results storage. It
does not cover runtime datatypes (variables, headers, csvpath match state,
metadata) — those are a different concern.

---

## 2. The reference syntax model

A v3 reference is a `$`-prefixed, dot-separated string:

```
$root_major.datatype.name_one[#name_two][.name_three]
```

`name_one` may carry a `#name_two` worksheet marker (files datatype only, for
XLSX files).

| Segment | Required? | Meaning |
|---|---|---|
| `root_major` | yes | The named object — a named-file name, named-paths group name, or named-results (run) name. |
| `datatype` | yes | One of `files`, `csvpaths`, `results`. |
| `name_one` | yes | See below — meaning differs sharply by datatype. |
| `name_two` | optional, files only | An XLSX worksheet identifier, written as `#worksheet_name` appended directly to name_one's path. |
| `name_three` | optional (for every datatype, per the current spec) | A more specific part of what name_one identified. |

The names `root_major`/`name_one`/`name_two`/`name_three` are inherited from
v1/v2's own naming for a related but larger structure — kept for continuity,
not because they're the clearest possible names.

### The name_one distinction — the load-bearing point of clarity

**name_one means structurally different things per datatype**, and getting
this right is the single most hard-won point in the whole design:

- **For `files` and `results`: name_one is a path-like prefix search.** It is
  built from `/`-separated segments (literal names, `*`, or a `:name("...")`
  function), and it identifies *which logical file* (files) or *which run*
  (results) — a location in a directory tree, matched by prefix.
- **For `csvpaths`: name_one is a version-selecting expression**, not a path.
  A named-paths group has exactly one `group.csvpath` file on disk, updated
  in place every time statements are (re)loaded; there is no per-version
  physical file. Versioning instead lives entirely in the group's own
  `manifest.json`, as an array of load events. So for csvpaths, name_one is a
  time/index/ordinal/UUID expression that selects one or more *entries in
  that manifest array* — every result shares the same `group.csvpath` path,
  differentiated only by UUID (the manifest entry's identifying UUID).

This is why the STRUCTURE table (below) lists name_one's per-datatype meaning
so differently, and it's why `csvpaths`'s finder (not yet built, see §6) will
have to work completely differently from the `files` finder that already
exists — name_one there is doing version-selection work, not path-matching
work.

### root_major, name_one, name_three — what limits each segment

- **root_major**: limited only by an exact name, `*` (all named-things), or a
  `:regex(...)` function.
- **name_one**: limited primarily by constructing the path (literal segments,
  `*`, `:name(...)`), but also by date, index, UUID, and other functions.
  Dates here are always *date of arrival* (files), *date of load* (csvpaths),
  or *date of run* (results).
- **name_three**: an identifier that combines with name_one to reach specific
  run-result files or values. Functions here reach "well known files" (e.g.
  `:errors()`) or drill into a specific value inside one (e.g.
  `:errors(:idchain("add[0]string[2]"))`).

### The STRUCTURE table

| Datatype | name_one | name_two | name_three (optional) | name_one alone means | name_three alone means |
|---|---|---|---|---|---|
| `files` | path (prefix search) | worksheet (XLSX) | version — index, fingerprint, or datetime | path to the named-file's file-home directory (dir of version files) | path to a specific version file |
| `csvpaths` | version — index, datetime, or UUID | (none) | csvpath statement ID (ID+UUID) | list of (path-to-`group.csvpath`, uuid) pairs, one per selected manifest version | bytes of the one csvpath statement identified, within the version identified |
| `results` | path (prefix search) | (none) | csvpath statement ID (path+UUID) | path to the run directory | path to a specific statement's result-subdirectory within the run dir |

Footnotes from the spec, worth keeping verbatim:
- csvpaths' name_three is a *statement ID*, not a separate file, because there
  is no per-statement file on disk for a csvpaths group — only a whole
  `group.csvpath` file. results' name_three is also a statement ID, but *is*
  a separate directory (each statement in a run gets its own result
  subdirectory with its own files) — same label, structurally different
  reason.
- The spec explicitly flags that there may be no further functions available
  for csvpaths' name_three beyond identity, though access to statement-level
  metadata (tags, modes) via a function is plausible future value, currently
  unbuilt.

---

## 3. Query vs. Resolve

v3, like v2, splits reference-following into two phases, but the phases mean
something different in v3.

**Query**: runs the reference as a search and returns 0-or-more results, each
a **file-system path + a UUID**. Cheap — no data is read.

**Resolve**: pulls actual content out of what query found. Resolving returns
bytes (if binary), or a string/JSON structure. It is possible for resolve to
have no answer (`None`) — e.g. a bare results reference with no metadata
pointer has no single well-defined "the" output of a run.

### Query, by termination point

**Query terminating at name_one** (regardless of which pointer function, if
any, ends the chain) is a **prefix search returning zero or more paths to
"file home" style container directories**:

| Datatype | What name_one-terminated query() returns |
|---|---|
| files | path to the named-file's file-home directory (directory of version files) |
| csvpaths | path to the `group.csvpath` file |
| results | path to the run directory |

**Query terminating at name_three**:

| Datatype | What name_three-terminated query() returns |
|---|---|
| files | path to the specific version file |
| csvpaths | path to the `group.csvpath` file (same path as always; the UUID is what differs) |
| results | path to the specific statement's instance directory within the run dir |

### Resolve — the three-way classification

A reference resolves to exactly one of three kinds of thing (`Reference3.
resolve_kind` in code: `FIRST_PARTY` / `METADATA_FILE` / `METADATA_FIELD`):

1. **First-party data** — the actual underlying content — returned when no
   function names metadata at all (e.g. a plain files reference with a
   version pointer resolves to that version file's raw bytes).
2. **A whole metadata file** — returned when a function names a known
   metadata file (`:errors()`, `:vars()`, `:meta()`, or an arbitrarily-named
   file via `:file(...)`) with no further drilling into it.
3. **One metadata field** — returned when that metadata-file function itself
   takes another pointer as its argument, extracting one value rather than
   the whole file (e.g. `:errors(:idchain("add[0]string[2]"))`).

The full resolve matrix from the spec, by termination point and pointer kind:

| | name_one, no pointer | name_three, no pointer | name_one, file pointer | name_three, file pointer | name_one, field pointer | name_three, field pointer |
|---|---|---|---|---|---|---|
| **files** | no default → `None` | version file bytes (name_three always points) | contents of `manifest.json`/`definition.json` | version file bytes | field from `manifest.json`/`definition.json` | not possible |
| **csvpaths** | no default | no default | contents of `manifest.json`/`definition.json` | no default (needs `:uuid(...)` + instance name/index for csvpath bytes) | requires `:uuid(...)`; returns a field, or (if only `:uuid(...)`) the version's bytes | requires `:uuid(...)` + instance name/index to get a field |
| **results** | no default | no default | contents of `manifest.json` | any standard run-result file, or a user-named parquet/jinja/text file, via e.g. `:file("orders.parquet")` | field from `manifest.json` | field from any standard JSON run-result file (`errors.json`, `meta.json`, etc.) |

**Note on `:uuid(...)`**: it is not a mandatory hand-typed function. If a
reference's own pointer (`:first()`, `:index(n)`, etc.) already narrows to
one version, nothing else is needed. `:uuid(...)` matters when a caller wants
to resolve one *specific*, previously-queried candidate — via `resolve_from
(list[str|UUID])` — out of several results a prior `query()` returned. This is
already how `resolve_from()` is implemented; no code changes were needed for
this point when it was worked out.

### The two-call workflow

```python
ref = ReferenceParser3(string="$acme.files.*.:last()", csvpaths=paths)
finder = FilesReferenceFinder3(csvpaths=paths, ref=ref)
results = finder.query()        # cheap: list of ReferenceResult3(path, uuid)
data = finder.resolve()         # or finder.resolve_from(narrowed_selection)
```

`resolve()` internally calls `resolve_from(self.query())` — it re-queries and
resolves everything. `resolve_from(selection)` accepts either a
`ReferenceResults3` (resolve exactly that set) or a `list[str | UUID]` (pull
just those out of a fresh `query()` first) — this is what makes "cheap
search, then selective fetch" real rather than aspirational, and is the shape
that lets an AI agent triage cheaply before paying for full data pulls.

---

## 4. Functions

Functions are the mechanism for narrowing and pointing within a reference.

**Form**: `:name(arg)` or `:name()` — a colon, a name, parentheses, at most
one argument. Functions chain with no separator (`:before(:yesterday()):
index(3)`) and are implicitly ANDed together.

**Arguments** can be a quoted string, a signed int, an `@name` runtime-bound
variable, a nested function call, a bare `*`, or a `/regex/` literal.

**Runtime lookup, not grammar knowledge**: the grammar has zero built-in
knowledge of what functions exist — `FNAME` is just `/[a-zA-Z_][a-zA-Z0-9_]*/`.
Every function name is resolved against a name-keyed registry
(`ReferenceFunctionFactory`) at transform/build time, not parse time. This is
the central design choice that keeps the grammar flat (v1/v2's huge
per-operator alternation is exactly what this avoids).

### Context-setter vs. pointer

Every function self-reports one of three roles:

- **Context setter** — narrows the current scope without resolving to a
  specific item (e.g. `:yesterday()`, `:quarter()`, `:before()`/`:after()`,
  `:all()`, `:name(...)`). *(You could make a case for `:name(...)` being
  a value, not a context).*
- **Pointer** — resolves the current scope down to exactly 0 or 1 item (e.g.
  `:last()`, `:first()`, `:index(5)`, `:uuid("...")`).
- **Value** — produces a value that can be used as the input to a function
  or as a segment of a path-like string. (e.g. `year()` can be used as
  `$acme.files.orders/:year()` to create a dynamic path like `acme/orders/2026`.)


There is deliberately **no "value extractor" role**. What a pointer
resolves to depends purely on *where it sits*:
- In name_one, a pointer resolves to a physical file, a named-paths group
  version, or a run.
- In name_three, a pointer resolves to a well-known metadata *file* (e.g.
  `:errors()`) — unless that pointer's own argument is itself another
  pointer, in which case it resolves to a specific *value* inside that file
  instead (e.g. `:errors(:idchain(...))`). Same trait, one nesting level
  deeper, not a separate category.

**Note on pointers within file functions:**
References are are as simple as we could make them without giving up value.
They are not intended to give the maximum flexibility in extracting
data. In the example above, `:errors(:idchain(...))`, the resulting value
is one or more error dicts with keys matching the given idchain. We don't
allow more than one key to be specified and there's no way to do boolean
predicates beyond what you see. In the usual case, if you need more
specificity than a reference gives it is your job to go beyond the basic
access references give you.

### At most one pointer per chain, per nesting level

A chain may contain any number of context setters but at most one pointer.
Critically, **a pointer used as another function's argument does not count
toward, or act as, the pointer of the chain it is nested in** — it resolves
that inner function's own internal scope. So `:errors(:idchain("..."))` is
legal (one pointer — `idchain` — at the argument level, one pointer —
`errors` — at the chain's own top level). Conversely, `:last():index(3)`
sitting side by side in the same chain is illegal (two pointers, same
level).

This rule is enforced in code by `ReferenceFunctionFactory.build_chain()`,
which compiles every call in a chain, then rejects the chain if more than one
compiled function has `ROLE == Function3.POINTER`.

### Why a trailing bare `*` is illegal but bare `:all()` is fine

This is real design reasoning, not an arbitrary restriction. `*` is a
**linguistic fragment**. A `*` says: "any of the data that ___". It names an
open set and something must follow to complete the sentence. The something
could be more path segments, a function on name_one's chain, or a name_three.
`:all()`, by contrast, is already a **complete instruction**. `:all()` says:
*"get me all of them!"* Nothing needs to follow it.

The two are not otherwise equivalent either (see the EXAMPLE SCENARIO in the
spec doc, summarized below): `*` **flattens** every wildcard position in the
reference into one pooled search space that a terminal pointer reduces to a
single answer; `:all()` anywhere in the reference **groups** — it switches
the *whole reference* into a mode where every wildcard position (root_major
included) becomes a dimension of a composite group key, and the terminal
function distributes across the resulting cross-product. Confirmed by a
worked example: given named-file `alpha` (paths `zero.csv` [1 version],
`one.csv` [2 versions]) and named-file `beta` (path `two.csv` [2 versions]):

- `$*.files.*.:last()` → 1 result (single most-recent file across everything —
  flattened).
- `$*.files.:all().:last()` → 3 results, one per (named-file, path) pair —
  grouped.
- `$alpha.files.*.:last()` → 1 result (root already literal, so nothing extra
  to flatten across, but still one pooled answer across alpha's paths).
- `$alpha.files.:all().:last()` → 2 results, one per path within alpha.

A related side finding baked into the same example: `:last()` means
*arrival/registration order* (manifest array order), **not** lexicographic
order on the version filename — version names are content hashes with no
inherent temporal order.

The precise illegality rule, as implemented in `Reference3.check_valid()`:
reject only when `name_three is None and not name_one.functions and
name_one.path[-1] is a bare Star3` — i.e. a **trailing, nothing-follows**
star with no way to complete it. A mid-path star (`$alpha.files.*/orders`) is
always fine — the literal segment after it supplies the completion. A star
followed by name_one's own function chain (`*:first()`) or by a name_three
is also fine.

#### Why `*` is disallowed as name_three's body, even though it is legal elsewhere

Settled 2026-08-11. `ResultsReferenceFinder3._name_three_selector()` rejects a
bare `Star3` body outright (`"does not support a bare '*' as name_three's
body -- use :all() instead"`), full stop — even combined with a trailing
function (e.g. `.*:errors()`), unlike name_one, where a mid-path or
function-followed `*` is fine per the rule above. This is not the same
"needs something to complete it" argument — a name_three's `*` here would
already have `:errors()` (or another accessor) following it, so the
sentence-completion problem does not apply.

The real reason: `*`'s flatten-vs-`:all()`'s-group distinction only means
anything where there is more than one axis/position for the two to diverge
on — name_one is a `/`-joined, multi-segment path, so a wildcard at one
position can coexist with literal segments at others, and pooling across
that wildcarded position (`*`) is genuinely different from grouping by it
(`:all()`). name_three's body is not a path at all — it is a single,
unstructured identity slot (a literal statement name, or the stringified
load-time index of an unnamed one). There is no second position for `*` to
wildcard against, so `*` and `:all()` would be exactly, unconditionally
synonymous there — always selecting every instance, never diverging. Rather
than give the same concept two spellings with zero cases where they would
ever differ, the language keeps one canonical form (`:all()`) and disallows
the other. This mirrors a pattern already followed elsewhere (e.g. a regex
argument has exactly one way to be written — passed directly as a `REGEX`
literal, never wrapped in a function of its own).

#### RESULTS' full depth model, and the one gap `:home()` fills

Settled 2026-08-10/11, arrived at over several rounds with real registered
data checked at each step, not just reasoned about. RESULTS' template depth
has exactly four positions in a 2×2 matrix (how many levels of nesting a
reference targets, crossed with pool-vs-group), plus one position that
turned out to need a fifth, different kind of function entirely:

| Depth | Pooled (one answer) | Grouped (one per distinct value) |
|---|---|---|
| zero levels (direct children, "no template") | bare pointer (`:last()`/`:first()`/`:index(n)`) | *(nothing to group by — no wildcarded position exists)* |
| exactly one level | `*` | `:all()` |
| any depth | `:flatten()` | `:groups()` |

`*`/`:all()` are peers restricted to exactly one wildcarded segment,
regardless of whether a pointer follows — this holds even without a
pointer (a pointer-less `:all()` still means "one level, unreduced," not
"any depth," a bug introduced then caught and fixed the same day it
shipped in PR #241 — the fix mistakenly mirrored csvpaths' own bare
`:all()` precedent, which does not apply to results since csvpaths has no
path dimension at all to be wrong about).

The gap: nothing above provides "every zero-level run, unreduced" — a bare
pointer always reduces to exactly one. `:all()`'s own one-level restriction
means it can never reach zero levels either. The fix is not a new pool/
group pair (zero levels has no wildcarded position, so there is nothing to
group by — only one mode is meaningful there, matching the empty cell in
the table above) — instead, `:home()`, an *existing* `VALUE`-role field
accessor (never a `POINTER`), fills it for free: when it is the only
function present in a bare chain, nothing reduces the candidate set, so
every matching zero-level run comes back unreduced — "everything that has
its home here." The moment a real pointer joins the chain (either order —
`:home():last()` and `:last():home()` mean the same thing), the pointer
reduces to one and `:home()` reverts to its ordinary job of reading the
field off whatever got selected. No new grammar, no order-sensitivity trap
(`:home()` never competes with a pointer for which one "wins" — it simply
is not a pointer).

`:home()` is root-only — there is no prefixed form (`$acme.results.beta/
:home()`). This was built, then removed the next day (2026-08-12): a plain
literal prefix segment with nothing trailing already means "every run
under this exact prefix, unreduced" (`$acme.results.beta` alone), and it
predates this whole depth refactor. Direct testing confirmed the prefixed
`:home()` shape gave byte-for-byte identical results to the plain prefix
in every case tried, with and without a trailing pointer — so it was pure
redundant code, a second, more confusing spelling of something that
already had one canonical spelling (the same "one canonical spelling"
principle behind disallowing `*` at name_three and the `:regex()` wrapper).
`:home()` is only load-bearing at the bare/root position, where the
grammar has no other way to express "zero segments" — a literal prefix
already covers every other depth.

---

## 5. What's actually built and tested today

Verified 2026-08-05: `pytest tests/references/ -q` → **486 passed**. Full
project suite: **2066 passed, 11 failed** — the 11 failures are the
pre-existing, unrelated SFTP/S3/Nos baseline (issue #216 and similar), not
references-v3 regressions.

### Grammar (`csvpath/references/reference_grammar_3.py`)

`REFERENCE_GRAMMAR_3`, a Lark grammar parsed with `parser="lalr"` (chosen
deliberately — LALR is required for `parse_interactive()`-based type-ahead,
see §7 — and confirmed genuinely unambiguous, not just convenient: an earlier
draft had a redundant, ambiguous "bare func_chain" alternative for name_one
that caused a real reduce/reduce collision on `COLON`; removing it fixed both
the ambiguity and the LALR incompatibility with no loss of expressiveness).
`QueryParser3` wraps it as a syntax-only parser (`.parse()`, `.validate_
query()`) — it does not build the object graph or enforce semantic rules;
that's the transformer's job.

Grammar shape: `reference: "$" root_major "." datatype "." name_one ("."
name_three)?`. `name_one` is a `/`-joined `path_prefix` (segments: `*`,
literal `PATH_SEGMENT`, or a whole `function`), optional `#name_two`, optional
trailing `func_chain`. `name_three` is either an optional literal/`*` body
plus optional trailing `func_chain`, or a bare `func_chain`. Function args:
`STRING`, `SIGNED_INT`, `AT_VAR` (`@name`), a nested `function`, a bare
`STAR`, or a slash-delimited `REGEX` (mirrors the REGEX/REGEX_INNER pattern
already used in `csvpath/matching/lark_parser.py`). There is deliberately no
bare/unquoted catch-all argument token (an earlier `BARE_ARG` was removed —
it was fully redundant with `REGEX`/`STRING`/`SIGNED_INT`/`STAR` once those
existed, and it could not represent regex capture groups without swallowing
the function's own closing paren).

name_three's required-ness is deliberately **not** encoded in the grammar at
all for any datatype (kept fully optional grammatically, everywhere) — this
is the main way v3 avoids the v1/v2 grammar's per-datatype rule explosion.

Tested by `tests/references/test_references_3_grammar.py` — grammar-level
positive/negative cases against the spec's own example corpus.

### Transformer and object graph

- **`reference_transformer_3.py`** — `Reference3Transformer(lark.Transformer)`,
  one method per grammar rule (in contrast to v1's `reference_transformer.py`,
  which has one method per grammar-rule *combination* and mutates a shared
  flat object — the pattern v3 is designed specifically to avoid). Modeled on
  `csvpath/matching/lark_transformer.py`.
- **`reference_3.py`** — the plain value-object graph the transformer builds,
  with no execution context or filesystem access:
  - `Star3` — a bare `*` wildcard token (all instances equal).
  - `Variable3` — an `@name` runtime-bound variable reference.
  - `Regex3` — a slash-delimited regex literal (pattern held without delimiters).
  - `FunctionCall3` — the raw parsed `:name(arg)` shape (not yet a real,
    behavior-having function — see `Function3` below). Has `contains_
    function_named(name)`, a purely structural recursive check over its own
    arg chain.
  - `NameOne3` — path (list of literal/`Star3`/`FunctionCall3` segments),
    optional `name_two`, list of trailing functions.
  - `NameThree3` — optional body (literal/`Star3`), list of trailing
    functions.
  - `Reference3` — the whole parsed reference: `root_major`, `datatype`,
    `name_one`, `name_three` (optional). Exposes `check_valid()` (see §4's
    bare-`*` rule — this is where it's enforced) and `resolve_kind` (the
    `FIRST_PARTY`/`METADATA_FILE`/`METADATA_FIELD` computation described in
    §3, currently driven by placeholder name-lists — `_METADATA_FILE_
    FUNCTIONS` and `_METADATA_FIELD_FUNCTIONS` — explicitly flagged in code
    comments as stand-ins for real per-function traits the `Function3`
    registry will eventually own).
  - Every object round-trips to its original string form via `__str__` — all
    47 positive examples in the spec/grammar corpus were confirmed to parse
    and reconstruct byte-for-byte through `ReferenceParser3` before the test
    suite was written.
- **`check_valid()` is called explicitly by `ReferenceParser3.parse()` after
  `Transformer.transform()` returns, not from inside a transformer rule
  method or `Reference3.__init__`** — deliberately, so a violation surfaces
  as a real `ReferenceException3`, not a Lark `VisitError` wrapping it (Lark
  wraps any exception raised inside a `Transformer` rule method; this was
  caught via direct testing, not assumed).

Tested by `tests/references/test_reference_3.py` and `tests/references/
test_reference_transformer_3.py`.

### `ReferenceParser3` (`csvpath/references/reference_parser_3.py`)

Wraps a reference string plus a required `csvpaths` context object. `__init__
(*, string, csvpaths)` — both keyword-only, both bounds-checked (`ValueError`
on `None`/empty). Parses eagerly in the constructor via a shared, lazily-
built, class-level `QueryParser3` instance (compiled once, not per instance).
Exposes `.parsed` (the `Reference3`), `.ref_string` (round-trip string),
`.root_major`/`.datatype`/`.name_one`/`.name_two`/`.name_three` passthrough
properties, and logs+re-raises on parse failure.

Tested by `tests/references/test_reference_parser_3.py`, including the
spec-corpus round-trip and the `check_valid()`/`VisitError` regression.

### Functions: `Function3` and `ReferenceFunctionFactory`

`Function3` (`csvpath/references/functions/function_3.py`) is the base class
for real, behavior-having functions — distinct from `FunctionCall3` (the raw
parsed shape). Declarative per-subclass metadata (`NAME`, `SUMMARY`, `ROLE`,
`DATATYPES`, `ARG_TYPES`, `ARG_REQUIRED`) drives a generic `check_valid()`
(structural only — required-ness, arg type, recurses into a nested `Function3`
arg) and a `describe()` method returning a self-description dict, feeding a
future type-ahead registry. Deliberately does **not** port `csvpath.matching.
functions.args.Args`/`ArgSet` — that machinery solves multi-arg-overload
problems these ≤1-arg functions don't have, and the requirements doc's own
hard rule (no code-sharing between the match language and reference language)
rules out importing it directly anyway.

`ReferenceFunctionFactory` (`reference_function_factory_3.py`) is the
name-keyed registry: `build(call: FunctionCall3) -> Function3` (recurses into
a nested `FunctionCall3` arg first, then validates), `build_chain(calls) ->
list[Function3]` (compiles a whole chain and enforces "at most one pointer
per chain" by counting `ROLE == Function3.POINTER` among the *direct*
compiled siblings — a pointer nested inside another function's arg has
already been compiled away and doesn't count), and `add_function(cls)` for
runtime registration of custom functions.

**Fourteen concrete functions exist**:

| Function | Role | Arg | What it does |
|---|---|---|---|
| `First3` | POINTER | none | Earliest-arriving item in the current scope. |
| `Last3` | POINTER | none | Most-recently-arriving item in the current scope. |
| `Index3` | POINTER | required `int` | Item at a 0-based position, in arrival order. (David confirmed the spec's earlier "`:index(7)` means the seventh file" wording was his own mistake — it is 0-based, so `:index(7)` means the eighth.) |
| `Name3` | CONTEXT_SETTER | required `str` | Matches an exact literal name at this position — built specifically because a real filename with a `.` in it (e.g. `"zero.csv"`) cannot be written as a bare `PATH_SEGMENT` (the grammar reserves `.` as the name_one/name_three separator). Wired in only as a name_one path segment, not name_three. Str-arg only for now — the grammar also permits `*`/`@var`/regex here, but those need machinery (wildcard-as-arg semantics, variable lookup, regex matching) not yet built. |
| `All3` | CONTEXT_SETTER | none | Explicitly asks for every match, unreduced — the complete-instruction counterpart to a bare `*` (which is a dangling fragment on its own, see §4's "Why a trailing bare `*` is illegal but bare `:all()` is fine"). For csvpaths specifically (no path dimension to group by), this collapses to a simple case: a chain with `:all()` and no pointer returns every version in the manifest, unreduced — this is how `CsvpathsReferenceFinder3` actually reaches "Name_one used alone == list of versions in the form: (path-to-group.csvpaths, uuid)" (STRUCTURE table). |
| `Manifest3` | VALUE | none | Resolves to the manifest data for the enclosing named-file/named-paths group — the whole raw `manifest.json` when name_one is bare/sole-content (`$acme.files.:manifest()`), or the matched entry/entries when combined with real path narrowing and/or a version pointer in name_three (files) or name_one's own combined chain (csvpaths) — see below. `ROLE` is `VALUE`, not `POINTER` — corrected after realizing `:manifest()` never narrows/selects anything itself, in any usage (see below). |
| `Definition3` | VALUE | none | Points at the enclosing named-file/named-paths group's own `definition.json` (its stored configuration — sources, `on_arrival` behavior, scripts, webhooks, etc). Only wired in for the bare, sole-content name_one shape — `definition.json` is a single dict (not an array like manifest.json), so there is no "filtered subset"/"matched entry" concept for it the way `:manifest()` now has. Genuinely optional (not currently versioned; a group/file never explicitly configured has none on disk at all), so resolving it gives `None` rather than raising when absent. `DATATYPES` is `FILES`/`CSVPATHS` only — named-results has no `definition.json` equivalent. (`Definition3`'s own `ROLE` was still wrongly `POINTER` until this pass too — missed in the earlier `Manifest3` fix, caught while re-checking every accessor function's role for consistency ahead of building the six below.) |
| `Errors3` | VALUE | none | The parsed contents of a run instance's `errors.json` — results-only. Rides alongside the identity/`:all()` selector already in name_three, does not select the instance itself. |
| `Vars3` | VALUE | none | The parsed contents of a run instance's `vars.json` — results-only. |
| `Meta3` | VALUE | none | The parsed contents of a run instance's `meta.json` — results-only. |
| `Data3` | VALUE | none | The raw bytes of a run instance's `data.csv` — results-only. Genuinely optional (only written if at least one line matched); resolves to `None` rather than raising when absent, same treatment as `Definition3`. |
| `Unmatched3` | VALUE | none | The raw bytes of a run instance's `unmatched.csv` — results-only. Genuinely optional (only written if at least one line was unmatched); resolves to `None` when absent. |
| `File3` | VALUE | required `str` | The raw bytes of an arbitrary user-named output file (e.g. a custom parquet/jinja/text file) in a run instance's own directory — results-only. Genuinely optional; resolves to `None` when absent. `check_valid()` additionally rejects any arg containing `/`, `\`, or `..` — a bare-filename-only guard against escaping the instance directory (skipped for an `InterpolatedString3` arg, whose actual text is not known until evaluation, which is deferred). |
| `Idchain3` | VALUE | required `str` | The first metadata-*field* function — addresses one specific entry within a well-known file's own array by the match component that produced it (e.g. `:errors(:idchain("add[0]string[2]"))`). Only meaningful nested as `Errors3`'s own argument (`Errors3.ARG_TYPES` widened to accept it specifically, not any `Function3`). Despite sounding like it walks a live Matcher parse tree, it does not — confirmed directly against the real `Error` class: `Error.to_json()`'s `"source"` field already holds exactly this chain string (`Matchable.my_chain`, computed once, at error time), so this is a plain field-match filter over `errors.json`'s list — the same idea as `:type()`'s still-queued manifest-field-filter design, just applied to a different well-known file, and confirmed by David directly ("idchains are essentially like `:type()`... it is just a field in a well-known JSON file"). Zero matches is a legitimate empty list, not `None` and not an error. |

Tested by `tests/references/functions/` (one test file per function, plus
`test_function_3.py` and `test_reference_function_factory_3.py`).

### `ReferenceFinder3` ABC and results containers

`ReferenceFinder3` (`reference_finder_3.py`) is an ABC taking `(*, csvpaths,
ref: ReferenceParser3)`. `query()` is `@abstractmethod` — each datatype's
storage layout differs enough that there's no generic implementation.
`resolve()` and `resolve_from(selection)` are shared (concrete) on the ABC:
`resolve()` = `resolve_from(self.query())`; `resolve_from` accepts either a
`ReferenceResults3` or a `list[str | UUID]` (narrows a fresh `query()` via
`ReferenceResults3.select()`), then calls the abstract `_extract_data()` on
each result to fill in `.data`.

`ReferenceResult3`/`ReferenceResults3` (`reference_results_3.py`) are pure
value containers — a `path`+`uuid`(+optional `data`), and a list of the same.
Deliberately not modeled on v2's `ReferenceResults`, which mixes "holds the
output" with "knows how to reach storage" (does its own manifest lookups).
`ReferenceResults3` supports `.files`/`.uuids` passthrough lists, `file_for_
uuid()`/`uuid_for_file()`/`data_for_uuid()` lookups, `.select(identifiers)`
(subset by path or uuid), and `.remove(result)` (in-place, `ValueError` if
absent, `list.remove()`-compatible). `__iter__` yields a **snapshot** (`iter
(list(self._results))`), specifically so a caller can iterate-and-remove in
the same loop without skipping entries.

Tested by `tests/references/test_reference_finder_3.py` and `test_reference_
results_3.py`.

### The finders: `FilesReferenceFinder3`, `CsvpathsReferenceFinder3`, `ResultsReferenceFinder3`

`csvpath/references/files_reference_finder_3.py` — grounded in the real
on-disk `manifest.json` schema (one flat, append-only JSON array per
named-file; each entry's `file_home` is the directory shared by all versions
of one logical file; arrival order is simply array order, confirmed not
sorted by the `time` field).

**Supports**: a literal `root_major` (named-file name); `name_one` as `*`,
literal path segments, or `:name("...")` segments (matched against
`file_home` relative to the named-file's home directory); `name_three`
resolving via `build_chain()` to exactly one pointer (`:first()`/`:last()`/
`:index(n)`) that picks *which version*; `resolve()` for `FIRST_PARTY`
content (reads raw bytes via `DataFileReader`, mirroring the pattern already
used in `csvpath/util/cache.py`).

**Explicitly rejects** (raises `ReferenceException3` rather than guessing):
`root_major == "*"` (every named-file — a different traversal problem);
the `#worksheet` (`name_two`) marker; any function-valued name_one segment
other than `:name(...)`; a literal `name_three` body (bypassing a pointer
entirely); a `name_three` that doesn't resolve to exactly one pointer.
`_extract_data()` is effectively unreachable for `METADATA_FIELD` today and
raises for that kind — no metadata-field functions are registered for files
yet. `METADATA_FILE` is reachable, but only for `:manifest()` — see below.

Tested by `tests/references/test_files_reference_finder_3.py`, including a
direct check against the spec's own EXAMPLE SCENARIO (`$alpha.files.*.:last()`
→ `one.csv`'s `0000000000abcdef.csv`, matching exactly).

### `:manifest()`/`:definition()` — the first metadata-file functions wired up

`resolve_kind` had classified `METADATA_FILE`/`METADATA_FIELD` since early in
this initiative, but no finder could actually act on either — both raised
unconditionally. `:manifest()` (`Manifest3`) is the first to close that gap,
chosen as the starting point because it needs nothing new: both finders
already read the exact manifest.json the function resolves to. `:definition()`
(`Definition3`) followed immediately after, once confirmed to be the
identical shape at the identical home directory (`NamedFileDescriber`/
`NamedPathsDescriber`, both `JSON_FILE = "definition.json"`) — different
resource, same everything else. (`ROLE` for both is now `VALUE`, corrected in
a follow-up pass — see the next section.)

- **Grammar shape, deliberately narrow**: only wired in as a name_one-
  terminal, *bare/sole-content* reference — `$acme.files.:manifest()`/
  `:definition()` or `$acme.csvpaths.:manifest()`/`:definition()` — no other
  path narrowing, no trailing chain, no `name_three`.
  `ReferenceFinder3._is_bare_pointer_reference(reference, name)` (shared on
  the ABC) detects this shape; both finders check it first in `query()` and
  route to the shared `ReferenceFinder3._query_well_known_file(home,
  filename)` when either matches — `filename` is derived directly from the
  matched function's own name (`f"{name_one.path[0].name}.json"`, so
  `:manifest()` → `manifest.json`, `:definition()` → `definition.json`),
  rather than duplicating a near-identical branch per function. `:definition()`
  combining with anything else (real path narrowing, a trailing chain,
  `name_three`) still falls through to the ordinary pipeline and raises — a
  deliberate scope limit (`definition.json` is a single dict, so there is no
  narrower thing to resolve to). `:manifest()` combining with real narrowing
  is now supported too — see the next section for how.
- **`:definition()` tolerates absence; `:manifest()` did not need to.**
  `definition.json` is genuinely optional — a named-file/group that was
  never explicitly configured has none on disk at all (confirmed against
  `NamedFileDescriber.get_json()`/`NamedPathsDescriber.get_json()`, which
  already return `{}` rather than raising for exactly this case) — and it is
  not currently versioned (always the single current definition, regardless
  of which version of the file/group is in scope; versioning description
  files is a real future need, not yet prioritized, per David). The shared
  `ReferenceFinder3._read_well_known_file(path)` reads raw bytes if the file
  exists, else returns `None` — reused as-is for `:manifest()` too (harmless
  there since manifest.json always exists once anything is registered), so
  neither finder needed a function-specific existence check.
- **Real bug found and fixed while wiring `:manifest()` in**: `Reference3.
  resolve_kind` only ever inspected `name_one.functions` (the trailing
  chain) when `name_three` was absent — but a "path-less, function-only"
  name_one (the same shape `:all()` already uses) puts its function in
  `name_one.path[0]`, not `.functions`. So `$acme.files.:manifest()` was
  silently misclassified as `FIRST_PARTY`. This was latent and harmless
  until now, since no metadata-file function existed to expose it. Fixed
  by having `resolve_kind` scan any function-valued `name_one.path`
  segment too, not just `.functions` — safe to widen, since an ordinary
  path-matching function like `:name(...)` never appears in
  `_METADATA_FILE_FUNCTIONS`/`_METADATA_FIELD_FUNCTIONS`, so this only lets
  the real metadata functions be seen, it doesn't change what gets flagged.
- **Where the paths come from**: `FileManager.named_file_home(name)` /
  `PathsManager.named_paths_home(name)` (both already used elsewhere in
  these finders) give the named-file's/named-paths group's own home
  directory; both `manifest.json` and `definition.json` live directly under
  it in either datatype. Results carry `uuid=None` — neither file is itself
  a registered version.

Tested by `functions/test_manifest_3.py`/`test_definition_3.py`,
`test_reference_finder_3.py` (`TestIsBarePointerReference`,
`TestQueryWellKnownFile`, `TestReadWellKnownFile`), `test_reference_3.py`
(the `resolve_kind` path-segment fix), and `TestManifestFunction`/
`TestDefinitionFunction` classes in both `test_files_reference_finder_3.py`
and `test_csvpaths_reference_finder_3.py` (including real-file round trips
through an actual file on disk, and the never-configured/`None` case for
`:definition()`, not just fakes).

### `:manifest()` becomes context-aware; `ROLE` corrected to `VALUE`

Surfaced while confirming the semantics of `:manifest()` combined with real
narrowing (David's own worked examples: `$acme.files.:manifest()`,
`$acme.files.orders.:manifest()`, `$acme.files.orders.:last():manifest()`)
before starting `ResultsReferenceFinder3` — two real corrections came out of
that check, both to already-shipped code, neither breaking anything
previously working.

- **`ROLE` was wrong from the start.** `:manifest()`/`:definition()` never
  narrow or select anything — even bare, `root_major` already fully
  identifies the one named-file/group, so `:manifest()` is only ever
  *accessing* it, not resolving scope down from multiple candidates. This
  never surfaced as a problem because the bare shape never competed with
  another pointer for `build_chain()`'s "at most one pointer per chain"
  slot. It became visible the moment `:manifest()` needed to sit *beside* a
  real version-selecting pointer in the same chain (e.g. `:last():manifest()`)
  — as `POINTER` it would have been double-counted, raising a false "two
  pointers" error even though nothing is actually narrowed twice. Fixed by
  changing `Manifest3`/`Definition3` to `ROLE = Function3.VALUE` — the same
  category a future computed value like `:year()` would use, and already
  excluded from `build_chain()`'s pointer count. Confirmed non-breaking: the
  bare-shape query()/`_extract_data()` branches never actually consulted
  `ROLE` for these two functions — the role value was purely descriptive
  until now.
- **`:manifest()`'s behavior needed to become context-aware — `:definition()`
  did not.** `manifest.json` is an array of many per-version entries;
  `definition.json` is a single dict. So `:manifest()` now means "the
  manifest data for whatever's currently in scope," resolved three different
  ways depending on how much narrowing is present in the same reference:
  - **Bare** (`$acme.files.:manifest()`) — the whole raw file, unchanged
    from before.
  - **Real path narrowing, no pointer** (`$acme.files.orders.:manifest()`,
    files; `$acme.csvpaths.:all():manifest()`, csvpaths) — every matching
    entry, unreduced, each as its own `ReferenceResult3` resolving to its
    own entry dict (native Python `dict`, not raw bytes — the spec's own
    "Following a reference" section already anticipates JSON-structure
    results, not only bytes).
  - **Path narrowing plus a real pointer** (`$acme.files.orders.:last()
    :manifest()`, files; `$acme.csvpaths.:last():manifest()`, csvpaths) —
    the single matched entry's dict.

  Mechanically: `FilesReferenceFinder3.query()`'s name_three handling
  relaxed from "exactly one pointer required" to "one pointer, *or* zero
  pointers if `:manifest()` is present" (`build_chain()` already guarantees
  at most one pointer on its own); when zero, every matched candidate comes
  back instead of raising. `_extract_data()` in both finders now checks
  whether the relevant function chain (name_three for files; name_one's own
  combined chain for csvpaths) contains `:manifest()` and, if so, looks up
  the entry by `result.uuid` via the new shared `ReferenceFinder3.
  _find_manifest_entry_by_uuid(manifest, uuid)` and returns it directly,
  instead of falling into the ordinary `FIRST_PARTY` raw-bytes/statement-text
  path. `CsvpathsReferenceFinder3._extract_data()`'s own pre-existing
  `next((entry for entry in manifest if entry["uuid"] == result.uuid), None)`
  was refactored to use the same shared helper (two real consumers now).
  `:definition()` needed none of this — a single dict has no "filtered
  subset"/"matched entry" concept to resolve to, so it stays bare-shape-only.
- This directly informs `ResultsReferenceFinder3`'s own deferred `:manifest()`
  wiring (still not built): results' `:manifest()` will need the same
  "context-aware, riding beside the real pointer" treatment, now proven out
  here first rather than solved for the first time on the harder datatype.

Tested by updated assertions in `functions/test_manifest_3.py` (`ROLE ==
VALUE`), new `TestManifestCombinedWithNameThree` in
`test_files_reference_finder_3.py`, and replaced/new tests in
`test_csvpaths_reference_finder_3.py`'s `TestManifestFunction` (the old
"combining with a pointer is two pointers" test was itself wrong once the
role was fixed, and was replaced with tests confirming the combination now
works and resolves correctly).

### `ResultsReferenceFinder3` — the third and last finder

`csvpath/references/results_reference_finder_3.py` — the STRUCTURE table's own
"deepest hierarchy," confirmed by real API research (`ResultsManager`,
`ResultsRegistrar`, `ResultRegistrar`, `ResultSerializer`, `ResultFileReader`),
not assumed. Unlike files (name_one picks *which file*, name_three picks
*which version*) and csvpaths (name_one alone is the version selector, no
literal path exists), results' name_one does **both** jobs at once — it is a
literal path-like prefix search *and* the run (version) selector, combined.

**Two legal `name_one` shapes**, matching the spec's own examples directly:
- **bare/function-only**, no literal path at all (`$acme.results.:all()`/
  `$acme.results.:last()`) — mirrors csvpaths exactly: the sole path
  "segment" is itself a version-selecting function. Every run discovered for
  the group is a candidate, regardless of how deep its own prefix happens to
  be — no path narrowing at all.
- **literal/`*`/`:name("...")` path segments plus a trailing function chain**
  (`$acme.results.customers/2025:first()`) — the templated case; narrows to
  runs whose own prefix matches.

Either way, every matching run is pooled into **one flat list first**
(mirroring how a bare `*` already flattens across every match for files,
rather than reducing per matched prefix separately — an actual bug in the
first draft of this finder, caught and fixed before it shipped), and the
combined chain's at most one pointer (`:first()`/`:last()`/`:index(n)`)
reduces that whole pool to one run — reusing `_apply_pointer` completely
unchanged, since it already works positionally on any list. No pointer →
every pooled run comes back, unreduced, each carrying its own real `uuid`
(read from that run's own `manifest.json`'s `"run_uuid"` field).

**How runs are actually discovered — not by walking directories.** The first
draft of this finder matched Files' approach: compile the path pattern, walk
real directories level by level. That has a fatal flaw David caught directly:
this finder cannot know how many literal path segments a group's real
template requires before reaching the run-directory level — the default
template can change over time (with no record kept of past defaults, a real
open gap), and it can be overridden per-run via the `template` argument to
the run method — so there is no reliable way to *count* the right number of
levels to descend.

The fix: don't count levels — read them directly from the **archive-root
`manifest.json`** (the same global, one-entry-per-csvpath-statement-
execution manifest the run-ordering experiment found unreliable *as an
ordering source*, owing to cross-group interleaving and stale entries for
deleted runs). Confirmed against a real entry David pasted, and against
v1/v2's own working equivalent (`csvpath/util/references/results_tools/
resolve_possibles.py`, which `results_reference_finder_2.py` delegates to):
every entry already carries `"run_home"`, the exact, already-resolved
absolute path a specific run's directory landed at, recorded at the moment
that run happened. That sidesteps needing to know the template at all — a
past run's `run_home` reflects whatever template was actually in effect for
*that specific run*, regardless of what the default is now or was overridden
to. Discovery: filter entries by `"named_paths_name"` matching the group,
dedupe `run_home` values (several statements per run share one), then
existence-check each one (`Nos(run_home).exists()`) to drop stale entries —
the same defense v2 already uses, and exactly what makes the manifest usable
here despite the ordering experiment's earlier finding (discovery, not
ordering, is a different, safe use of the same data). The path pattern (for
the literal-path shape) is then applied as a **filter** over the discovered
`run_home` list — matching everything between the group's home directory and
the run directory's own name (the final path segment, stripped before
comparing) — rather than as something to walk. A field also present on real
entries but not needed for this — `"template"`, the literal template string
in effect for that specific run — could matter for future work (e.g.
interpreting which path segments are literal vs. date-derived per run), per
David's own note; not used yet.

**`name_three`** is an identity lookup into the selected run's own instance-
directory listing (one subdirectory per csvpath statement, named by that
statement's own identity — the same convention as csvpaths'
`named_paths_identities`, confirmed via `ResultSerializer.get_instance_dir`)
— reuses `_find_by_identity` unchanged — or `:all()` for every instance in
the run. Each matched instance carries its own real `uuid` too (read from
*its own* `manifest.json`'s `"uuid"` field, a different file one level
deeper than the run's).

**Well-known instance-level file functions are now wired in**: `:errors()`/
`:vars()`/`:meta()` resolve to parsed JSON (`errors.json`/`vars.json`/
`meta.json`); `:data()`/`:unmatched()` resolve to raw bytes (`data.csv`/
`unmatched.csv`), genuinely optional — `None` rather than raising when never
written (only written if at least one matched/unmatched line existed);
`:file("...")` resolves an arbitrary user-named output file the same
tolerant way, with a bare-filename-only guard rejecting `/`, `\`, or `..` in
the argument. All six are `VALUE`-role (they never narrow/select — see §5's
functions table) and ride *alongside* the identity/`:all()` selector already
occupying name_three, rather than replacing it — `ResultsReferenceFinder3.
_name_three_selector` now returns `(identity, match_all, accessor)`,
validating that an accessor always has an identity or `:all()` to apply to
(raises if neither is present — an accessor alone does not select an
instance) and that identity and `:all()` are never combined (contradictory).
`_extract_data()` dispatches by accessor name to the right file and read
mode (JSON vs. raw bytes) via a small shared table.

**`:idchain()` filtering `:errors()`**: `Errors3.ARG_TYPES` was widened to
accept a nested `Idchain3` call specifically (not any `Function3`) —
`:errors(:idchain("add[0]string[2]"))` filters the parsed `errors.json` list
down to entries whose own `"source"` field matches, per the confirmed real
`Error.to_json()` shape (see §5's functions table). Note this classifies as
`METADATA_FIELD`, not `METADATA_FILE` (`Reference3.resolve_kind` — a nested
pointer-like arg), so `_extract_data()` handles both kinds identically from
the point an accessor is found — `_read_accessor` already does the idchain
filtering internally based on `accessor.arg`. Zero matches is a legitimate
empty list.

**`:manifest()` now wired in for results too** — rides beside the run-
selecting pointer in name_one (`$acme.results.customers/2025:first()
:manifest()`, or the bare shape's `$acme.results.:last():manifest()`),
per the STRUCTURE table's "Resolve terminating at name_one, with file
pointer: results: contents of manifest.json" row. Unlike files/csvpaths,
there is no "filtered list vs. single entry" split to handle here — a run's
own `manifest.json` is already a single dict, not an array, so every
matched run (whether reduced to one by a pointer or left as many)
independently resolves to its own dict, via the same per-result `resolve()`
loop already established. Detected structurally
(`ResultsReferenceFinder3._combined_name_one_calls`, a new helper shared by
`query()`'s pointer-detection and `_extract_data()`'s manifest-detection,
factoring out the bare-vs-literal-path branching that used to be duplicated)
rather than relying on `resolve_kind` alone, to avoid conflating it with an
unrelated `METADATA_FILE` classification coming from a name_three accessor.
Combining `:manifest()` on name_one with a name_three selector is explicitly
rejected (raises) — a run's manifest and a specific instance are two
different things to ask for at once, not a supported combination.
**`:definition()` does not apply to results at all** — confirmed, not
newly discovered: named-results has no `definition.json` equivalent
(`Definition3.DATATYPES` already excludes `RESULTS` — see §5), so there is
nothing to wire in here.

Tested by `tests/references/test_results_reference_finder_3.py` — a fake
archive-root manifest.json plus real directory trees under `tmp_path` for
run/instance-level manifests (there is still no per-group manifest array,
only the archive-wide one), covering both `name_one` shapes, path matching
(literal/`*`/`:name(...)`), the now-correctly-empty under-specified-path
case, discovery specifics (dedup, stale-entry dropping, other-groups'
entries ignored, no archive manifest yet), the version pointer, `name_three`
identity lookup and `:all()`, every well-known-file accessor (parsed-JSON
and raw-bytes cases, absence tolerance, `:file("...")`'s path-traversal
rejection, an accessor combined with `:all()` reading each matched
instance's own file), the new `name_three` validation rules (accessor
with no identity/`:all()` raises; identity combined with `:all()` raises),
`:idchain()` filtering `:errors()` (a match, no match, both classified
correctly despite landing on `METADATA_FIELD` not `METADATA_FILE`), and
`:manifest()` on name_one in both shapes, with and without a pointer, and
its rejection when combined with name_three.

### `{...}` string interpolation — parsing/validation only

New scope, not in the original spec doc: since a function takes at most one
argument, there is no way to write a `:concat()`. Interpolation is the
mechanism instead — `:name("partner-{@company}-orders")`, `:name("partner-
{:year()}-orders")`, `:name("partner-{:year()}-{@company}")`. Only a bare
`@variable` or a call to a `VALUE`-role function is legal inside `{...}` —
a context-setter or pointer (e.g. `:first()`, `:all()`) is rejected, since
neither produces a plain value. `{{`/`}}` escapes a literal brace, matching
the convention already used by `csvpath/util/var_utility.py`'s `substitute()`.

**Deliberately split into two phases** (David's call: "(b) works for me" —
parsing/validation now, evaluation deferred): actually resolving an
interpolated string into its final text needs a runtime `CsvPaths` context
(to look up `@variable` values) and at least one real `VALUE`-role function
(e.g. a future `:year()`) — neither exists yet, so this phase only builds
and validates the *shape*.

- **`InterpolatedString3`** (`reference_3.py`) — holds `parts: list` (a mix
  of literal `str` chunks and `Variable3`/`FunctionCall3` sub-expressions).
  `check_valid()` rejects an unknown function name or a non-`VALUE`-role
  function found inside any `{...}` span. `__str__` round-trips exactly,
  including re-escaping literal braces back to `{{`/`}}`.
- **`Function3.VALUE`** — a third role alongside `CONTEXT_SETTER`/`POINTER`
  (see §4), now a real code constant, not just documented. `Function3.
  check_valid()` auto-widens any `str`-typed `ARG_TYPES` to also accept
  `InterpolatedString3`, so every existing/future string-taking function
  transparently supports interpolation with no per-function change needed.
- **A separate, small Lark grammar** (`_INTERPOLATION_GRAMMAR_3` in
  `reference_transformer_3.py`) parses one already-found `{...}` span's
  *content* — reusing the main grammar's terminal definitions verbatim
  (`AT_VAR`, `FNAME`, `function`, `arg`, `STRING`, `SIGNED_INT`, `REGEX`,
  `STAR`) to avoid behavioral drift, rather than touching
  `REFERENCE_GRAMMAR_3` itself. `_split_interpolated_parts` finds each span
  (deliberately simple: next unescaped `}` after an unescaped `{`, not a
  brace-depth/quote-aware balancer — sufficient for the shapes actually in
  use). A plain string with no unescaped `{` is left as a bare `str` (no
  `InterpolatedString3` wrapper) — the overwhelmingly common case.
- **`ReferenceFunctionFactory.get_registered_class(name)`** — returns the
  registered `Function3` *class* (or `None`) without constructing/validating
  an instance, so `InterpolatedString3.check_valid()` can check `ROLE`
  without triggering evaluation. Uses a **local import** inside `check_
  valid()` (`functions/` already depends on `reference_3.py` at module
  level, so importing the registry back at module level here would be
  circular — this is the one narrow, unavoidable exception).
- **`ReferenceParser3.parse()` unwraps `lark.exceptions.VisitError`** — any
  exception raised inside the `STRING` terminal transform method (e.g. an
  unescaped, unbalanced brace) arrives wrapped in Lark's own `VisitError`;
  `parse()` now catches it and re-raises `e.orig_exc` so callers see a plain
  `ReferenceException3`. This is the second time this exact class of bug has
  been hit in this project (the first, `Reference3.check_valid()`, was
  solved by moving the check outside `transform()`'s call stack entirely —
  not possible here, since the error originates from inside the terminal
  handler itself).
- **Fixed in the same pass**: a round-trip bug in `Reference3`'s arg-to-
  string rendering (`_arg_to_string`) — a plain `str` arg containing only
  escaped braces (e.g. originally `"literal {{brace}} text"`) was being
  unescaped on parse but not re-escaped on `__str__`, breaking round-trip.

Tested by `tests/references/test_reference_3.py` (`TestInterpolatedString3`,
`TestFunctionCall3` recursion cases), `test_reference_transformer_3.py`
(`TestStringInterpolation` — structural parsing only, no registry involved),
`test_reference_parser_3.py` (`TestStringInterpolationThroughParser` — full
pipeline, including the `VisitError`-unwrap regression and rejection of a
real `POINTER`-role function), and `functions/test_function_3.py` (the
`str`→`InterpolatedString3` auto-widening).

---

## 6. Known gaps / discrepancies between spec and implementation

The one substantive disagreement this section used to describe — `Files
ReferenceFinder3.query()` returning one result per manifest version instead
of one per distinct file-home directory when `name_three` is absent — is
resolved. `query()` now groups `candidates` by `file_home` and returns one
`ReferenceResult3` per distinct directory, with `uuid=None` (a directory
isn't a specific registered version, so it has no uuid of its own —
`ReferenceResult3.uuid` is now nullable to allow this). `_extract_data()`
was updated to match: resolving a name_one-terminal (no `name_three`) result
gives `None` (no default), rather than attempting to read a directory as a
file. See `tests/references/test_files_reference_finder_3.py::
TestNameThreeAbsent` and `tests/references/test_reference_results_3.py::
TestReferenceResult3::test_allows_none_uuid`.

**Other discrepancies/loose ends worth flagging:**

- `more_reference_queries.txt` uses a literal `INTERSECT` between two full
  reference expressions in two of its example queries, but the main spec
  still describes NOT/UNION/INTERSECT-combining (`ReferenceExpression`) as
  explicit "later phase" work. This has been explicitly deferred (confirmed
  staying later-phase), so the two example queries should be read as
  aspirational, not as evidence INTERSECT needs to move up in priority.
- `Reference3.resolve_kind`'s `_METADATA_FILE_FUNCTIONS`/`_METADATA_FIELD_
  FUNCTIONS` are hardcoded name tuples (`"errors"`, `"vars"`, `"meta"`,
  `"data"`, `"unmatched"`, `"file"`, `"definition"`, `"manifest"` /
  `"idchain"`). Every name in both tuples is now backed by a real,
  registered `Function3` (see §5's functions table) — `METADATA_FIELD` is
  reachable today via `:errors(:idchain(...))`, the one concrete case built
  so far. (An earlier version of this note guessed idchain was a different
  concept from the queued `:type()` field-accessor design, since it
  "indexes a parse tree" — confirmed wrong directly against the real
  `Error` class and by David: it is the same field-filter idea, just
  applied to `errors.json` instead of `manifest.json`.)

---

## 7. Not yet built at all

- **`CsvpathsReferenceFinder3` / `ResultsReferenceFinder3`** — only
  `FilesReferenceFinder3` exists. Real-API research (against `PathsManager`/
  `ResultsManager`) has confirmed genuine structural divergence worth knowing
  before building these: for csvpaths, name_one **is** the version pointer
  and name_three is an identity lookup into `named_paths_identities`
  (reversed from files' division of labor); for results, name_three
  overloads both identity *and* a well-known-file function in one go. A
  csvpaths `ReferenceResult3.path` is always the same physical `group.
  csvpath` path — only `uuid` (the manifest entry's own UUID) actually
  distinguishes versions there, so `file_for_uuid()`/`uuid_for_file()` are
  not meaningful for csvpaths specifically the way they are for files/
  results. `CsvpathsReferenceFinder3` (built after this document was first
  written — see below) confirmed both pieces of shared logic actually do
  generalize: pointer application (`:first()`/`:last()`/`:index()`
  list-position logic) and "resolve an identity against a list of (identity,
  item) pairs" now both live on the `ReferenceFinder3` ABC as
  `_apply_pointer`/`_find_by_identity`, shared by files and csvpaths.
- **`CsvpathsReferenceFinder3` is now built** — `name_one`/`name_three`'s
  roles are reversed from files: `name_one` **is** the version selector here
  (its combined function chain may hold at most one pointer — none present
  means every version in the manifest comes back unreduced, which is how
  "Name_one used alone == list of versions in the form: (path-to-group.
  csvpaths, uuid)", STRUCTURE table, is actually reached); `name_three` is
  an identity lookup into that version's `named_paths_identities`.
  Resolving a named/indexed statement gives its source text; resolving
  with no `name_three` gives `None` (a whole group version has no single
  unambiguous payload — the STRUCTURE section and the "Query vs. Resolve"
  matrix used to disagree about this specific case; confirmed and the doc
  fixed to say "bytes of the identified statement," not "no default").
  Scoped as narrowly as files was — `root_major == "*"`, `#worksheet`,
  literal/`*` path-building in `name_one`, and a function chain on
  `name_three` all raise rather than guess.
- **`ResultsReferenceFinder3` is now built** — see §5. Its run-ordering
  question (what determines a run's "arrival order," given results has no
  run-by-run manifest array the way files/csvpaths do) was resolved first,
  by a controlled experiment, not decided in the abstract: run directories
  are named `%Y-%m-%d_%H-%M-%S[_N]`, already lexicographically sortable =
  chronological, and a separate archive-wide global manifest (appended once
  per csvpath-statement execution, shared across every named-paths group,
  and found to retain stale entries for deleted runs) turned out to be
  unnecessary and untrustworthy for this — the finder scopes to the
  group's own directory and sorts its listing, exactly matching what the
  existing v1/v2 code already does (`ResultsManager.get_named_results()`'s
  non-template branch). No new run-by-run manifest was needed.
- **Functions beyond the fourteen listed in §5** — `:before()`/`:after()`,
  `:yesterday()`, `:quarter()`, `:date()`, `:time()`, `:uuid()`, `:regex()`,
  `:choice()`, `:names()`, `:message()`, `:count()`, `:above()`,
  `:has_errors()`, `:type()`, `:at()`, `:from()`/`:to()` — all appear in the
  spec/example-queries docs but have no `Function3` subclass yet.
  (`:errors()`/`:vars()`/`:meta()`/`:data()`/`:unmatched()`/`:file()`/
  `:idchain()` are done now — see §5.)
- **`root_major == "*"` traversal** — querying across every named-file/
  named-paths-group/named-result — explicitly rejected today by both
  `FilesReferenceFinder3` and `CsvpathsReferenceFinder3` as a "different
  traversal problem," not attempted.
- **`:all()`'s flatten-vs-group query semantics, only partially wired in.**
  `:all()` is now a real, registered function (`All3`, see §5), and
  `CsvpathsReferenceFinder3` handles its simple case correctly (no path
  dimension to group by there, so "no pointer" already means "return
  everything"). But the full cross-product/grouping behavior the spec's
  worked example describes for files (`$*.files.:all().:last()` → one
  result per named-file+path pair) needs `root_major == "*"` traversal,
  which — per the point directly above — doesn't exist yet. `Files
  ReferenceFinder3` does not yet accept `:all()` as a name_one path
  segment at all (`_compile_path_pattern` only recognizes `:name(...)`
  there today).
- **Type-ahead** — a prototype exists (`references_notes/autocomplete_
  prototype.py`) demonstrating the intended mechanism: Lark's `parse_
  interactive()`/`InteractiveParser.choices()` against actual LALR parser
  state, layered with a function registry filtered by datatype and slot
  (name_one path-slot vs. name_three part-slot) — deliberately in place of
  v1/v2's hand-maintained follow-set lists. It predates the grammar that
  actually got merged (written against a draft `reference_v3.lark` with
  different terminal names) and is not wired into the real grammar or
  `Function3`/`describe()` metadata at all. `REFERENCE_GRAMMAR_3` has been
  separately confirmed to work under `parser="lalr"` (a prerequisite for
  this technique), but no `parse_interactive()`-based code exists in
  `csvpath/references/` itself yet.
- **`ReferenceExpression`** (NOT/UNION/INTERSECT combining multiple
  references) — explicitly named in the spec as later-phase, confirmed
  still out of scope.
- **`{...}` interpolation evaluation** — parsing/validation is built (see
  §5), but actually resolving an `InterpolatedString3` into its final text
  is not. Needs two prerequisites that don't exist yet: variable resolution
  (looking up an `@name` against a real `CsvPaths`/scope context) and at
  least one real `VALUE`-role function (e.g. a future `:year()` — no
  `VALUE`-role function is registered today, only `CONTEXT_SETTER`/
  `POINTER` ones).
