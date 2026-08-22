# CsvPath References v3 — Compendium

A standalone definition of the References v3 subsystem, synthesized directly
from the persisted spec, requirements notes, example queries, and the actual
implementation and test code — originally as of 2026-07-31, caught back up
to 2026-08-19 in a dedicated pass (§5's later subsections, from "`_check_
position()`" onward, plus §6/§7). This document does not reconstruct any
chat history — where a design point was worked out through back-and-forth,
only the resulting, settled fact is stated here (the full design record,
including corrections narrated inline, lives in `specs/references_v3/notes/`
and `specs/references_v3/spec/references_expressions.md`).

Sources read to produce the original document:
- `specs/references_v3/notes/
creating references v3.txt` (the frozen/current spec, most recently revised
by David)
- `specs/references_v3/spec/requirements_for_functions.md`
- `specs/references_v3/notes/more_reference_queries.txt`
- `specs/references_v3/notes/autocomplete_prototype.py`
- all of `csvpath/references/` (grammar, transformer, object graph, parser,
exceptions, finder ABC, results container, functions subpackage, the one
concrete finder)
- all of `tests/references/`
- and this project's own persisted design-memory files.

The 2026-08-19 catch-up pass author additionally read:
- `specs/references_v3/notes/manifest_field_functions_proposal.md`
- `specs/references_v3/spec/references_expressions.md`
- `specs/references_v3/spec/normative_reference_examples.txt`
- and the full current `csvpath/references/` tree/test suite as they now
stand.

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

**v3 is a from-scratch replacement**, motivated by two things:
- v1/v2 have real tech debt and lack conceptual clarity
- and the vision of a more robust reference language giving an AI assistant
a single, concise, general-purpose exploration tool for digging into CsvPath
project state, instead of requiring many narrow, brittle, purpose-built tools.

v3 is **AI-facing only, for now**. v1/v2 stay exactly where they are, untouched,
and remain what end users see (identifying runs, registrations, named-paths
loads). v3 lives in a new location — `csvpath/references/` (top-level, not
under `util/`) — and follows v1/v2's own naming convention: `_3.py` files,
`3`-suffixed class names (`ReferenceParser3`, not `ReferenceParserV3`). Tests
live in `tests/references/`.

v3 covers only named-file, named-paths-group, and named-results storage. It
does not cover the four runtime datatypes (variables, headers, csvpath match
state, metadata) — those will be addressed in a follow-on release post v3's
launch.

---

## 2. The reference syntax model

Like v1/v2, a v3 reference is a `$`-prefixed, dot-separated string:

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
v1/v2's naming and are kept for continuity and because they make sense in
context even though they aren't obvious names. v1/v2 also allows for a
`name_four` based on a separator, `#` as is used to create name_two. `name_four`
has minimal use cases, is rarely used, and is only applicable to the runtime
datatype `variables`. It does not make an appearance in v3.

### The easy parts: `root_major` and the datatype

`root_major` is the name of a named-file, named-paths group, or named-results.
It can take a wildcard as explained below. The datatype is a static field
indicating which type of named-thing the reference is to. One of `files`,
`csvpaths`, or `results`.

### The name_one distinction — the load-bearing point of clarity

**name_one means structurally different things per datatype**, and getting
this right is the single most hard-won point in the whole design:

- **For `files` and `results`: name_one is a path-like prefix search.** It is
  built from `/`-separated segments. A segment is:
  - a literal name
  - `*`
  - a `:name("...")` function that may include a `.` char which would
    otherwise be illegal.
  Note that a regex in root_major can stand alone, but in name one and name
  three the `:regex()` function must be used.

  Segments identify *which logical file* (files) or *which run* (results) —
  a location in a directory tree, matched by prefix. Note that a prefix can
  `''`, i.e. no prefix. This is the case when no template is used during
  file registration or when a run is triggered. Using templates is an optional
  tool for semantically organizing files. If no template is used registrations
  and runs are found directly under their name's home directory. We speak of
  1-level templates, 2-level templates, etc. to describe how many path
  segments the template adds to the path to the home directory.
- **For `csvpaths`: name_one is a version-selecting expression**, not a path.
  A named-paths group has exactly one `group.csvpath` file on disk, updated
  in place every time statements are (re)loaded; there is no per-version
  physical file. Versioning instead lives entirely in the group's own
  `manifest.json`, as an array of load events. So for csvpaths, name_one is a
  time/index/ordinal/UUID expression that selects one or more *entries in
  that manifest array* — every result shares the same `group.csvpath` path,
  differentiated only by UUID (the manifest entry's identifying UUID).

This is why the STRUCTURE table (below) lists name_one's per-datatype meaning
so differently, and it's why `csvpaths`'s finder works quite differently from
the `files` and `results` finders.

### The role of functions

Functions look like `:name_of_function()` and can take 0 or 1 argument, which
is a string, number, function, or regex string wrapped in forward slashes,
like: `/.../`.

There is much more information on functions below in their own section.

### root_major, name_one, name_three — what limits each segment

- **root_major**: limited only by an exact name, `*` (all named-things), or a
  regex string wrapped in forward slashes, like: `/.../`.
- **name_one**: limited primarily by constructing the path (literal segments,
  `*`, `:name(...)`), but also by date, index, UUID, and other functions.
  Note that dates here are always evaluated as:
  - for `files`: date of arrival
  - for `csvpaths`: date of load
  - or for `results`: date of run
- **name_three**: an identifier that combines with name_one to reach specific
  run-result files or values, as in:
  - for `files`: a specific cryptographically identified version of a file
  - for `csvpaths`: a csvpath statement contained in a named-paths group
  - or for `results`: the specific results of running a csvpath statement
    contained in the named-paths group that was used in the run; i.e. a
    component result of the total set of run results.
  Functions in name three:
  - retrieve files (e.g. `:errors()`)
  - match a specific metadata value to select a file path (e.g.
    `:errors(:idchain("add[0]string[2]"))`)
  - retrieve a specific metadata field (e.g. `:uuid()`)

### The STRUCTURE table

| Datatype | name_one | name_two | name_three (optional) | name_one alone means | name_three alone means |
|---|---|---|---|---|---|
| `files` | path (prefix search) | worksheet (XLSX) | version — index, fingerprint, or datetime | path to the named-file's file-home directory (dir of version files) | path to a specific version file |
| `csvpaths` | version — index, datetime, or UUID | (none) | csvpath statement ID (ID+UUID) | list of (path-to-`group.csvpath`, uuid) pairs, one per selected manifest version | bytes of the one csvpath statement identified, within the version identified |
| `results` | path (prefix search) | (none) | csvpath statement ID (path+UUID) | path to the run directory | path to a specific statement's result-subdirectory within the run dir |

Note: `csvpaths` name three is a *csvpath statement ID*, not a separate file.
There is no per-statement file on disk for a csvpaths group, only a whole
`group.csvpath` file with `---- CSVPATH ----` delimiters between the ordered
csvpath statements in the group. `results` name_three is also a statement ID,
but it *is* a separate directory (each statement in a run gets its own result
subdirectory with its own files).

---

## 3. Query vs. Resolve

v3, like v2, splits reference-following into two phases, but the phases mean
something different in v3.

**Query**: runs the reference as a search and returns 0-or-more results. Each
is the set of:
- a file-system path
- a UUID
- a name two (Excel files only, and optionally)
- an instance ID (`csvpaths` only, and optionally)

These results always point to a file system location, with the identifiers
needed for any internal file pointer (for Excel and `group.csvpaths`). This
is the case even when the reference is clearly pointing to a metadata field
within that context. In the query stage, a user can trim the list of results
according to path, UUID, etc. without accessing whole files. In some cases
a reference expression may combine two references, when both sets of results
are comparable without further resolution.

**Resolve**: pulls actual content a reference points to. When a reference
points to a file, resolving returns either bytes (if the reference is to a
binary file, such as an `.xlsx`) or a JSON structure. When a reference
points to a field the return is a string, int, date, UUID, etc.

It is possible for resolve to return no answer (`None`). A bare results
reference with no metadata pointer has no single well-defined resolve output
of a run; only the path to the run is indicated and that is available in the
query stage.

### Query, by termination point

A Query terminating at name_one (regardless of any pointer function) is primarily a path,
which may be resolved to a value, if further resolution of the reference is possible.

| Datatype | What name_one-terminated query() returns |
|---|---|
| files | path to the named-file's file-home directory (directory of version files) |
| csvpaths | path to the `group.csvpath` file |
| results | path to the run directory |

**Query terminating at name_three**:

| Datatype | What name_three-terminated query() returns |
|---|---|
| files | path to the specific version file |
| csvpaths | path to the `group.csvpath` file (same path as always; the combined version UUID and statement ID differ) |
| results | path to the specific statement's instance directory within the run dir |

### Resolve — the three-way classification

A reference resolves to a 0 or more set of one of three kinds of thing:

1. **First-party registered data** — the actual underlying content — returned
   when no function names metadata at all (e.g. a plain files reference with a
   version pointer resolves to that version file's raw bytes).
2. **A whole results metadata or data file** — returned when a function names
   a known metadata file (`:errors()`, `:vars()`, `:meta()`, or an arbitrarily-
   named file via `:file(...)`) with no further drilling into it.
3. **A manifest.json or definition.json file** — file contents of one of the two
   main config files. Note all datatypes have `manifest.json` but only `files`
   and `csvpath` have `definition.json`.
4. **One metadata field** — returned when config file function or run metadata
   file function itself takes another pointer as its argument, extracting one
   value rather than the whole file (e.g. `:errors(:idchain())`).

Note that a file accessor that takes a field accessor is doing one of two things:
- if the field accessor has no argument it returns the field's value
- if the field has an argument, it limits the reference's match to files that
contain fields with exactly that value. In this case, the resolved reference
returns the file, not the field, because the field is just a predicate, not a
retrieval. It is not possible to pass multiple limiting field values to a
reference as a way to be more discriminating. This is an intentional
simplification. Reference expressions offer one approach to further narrowing.

The full resolve matrix by termination point and pointer kind:

| | name_one, no pointer | name_three, no pointer | name_one, file pointer | name_three, file pointer | name_one, field pointer | name_three, field pointer |
|---|---|---|---|---|---|---|
| **files** | no default → `None` | version file bytes (name_three always points) | contents of `manifest.json`/`definition.json` | version file bytes | field from `manifest.json`/`definition.json` | not possible |
| **csvpaths** | no default | no default | contents of `manifest.json`/`definition.json` | no default (needs `:uuid(...)` + instance name/index for csvpath bytes) | requires `:uuid(...)`; returns a field, or (if only `:uuid(...)`) the version's bytes | requires `:uuid(...)` + instance name/index to get a field |
| **results** | no default | no default | contents of `manifest.json` | any standard run-result file, or a user-named parquet/jinja/text file, via e.g. `:file("orders.parquet")` | field from `manifest.json` | field from any standard JSON run-result file (`errors.json`, `meta.json`, etc.) |

**Note on `:uuid(...)`**: it is not a mandatory function. If a reference's
own pointer (`:first()`, `:index(n)`, etc.) already narrows to one version,
nothing else is needed. `:uuid(...)` matters when a caller wants to resolve
one *specific*, previously-queried candidate — via `resolve_from
(list[str|UUID])` — out of several results a prior `query()` returned.

### The two-call workflow

```python
ref = ReferenceParser3(string="$acme.files.*.:last()", csvpaths=paths)
finder = FilesReferenceFinder3(csvpaths=paths, ref=ref)
results = finder.query()        # cheap: list of ReferenceResult3(path, uuid)
data = finder.resolve()         # or finder.resolve_from(narrowed_selection)
```
In this case, above, the resolve returns the paths to the last instance home
within every 1-level template run.

---

## 4. Functions

Functions are the mechanism for narrowing and pointing within a reference.

**Form**: `:name(arg)` or `:name()` — a colon, a name, parentheses, at most
one argument. Functions chain with no separator (`:before(:yesterday()):
index(3)`) and are implicitly ANDed together without regard for order.

**Arguments** can be a quoted string, a signed int, an `@name` runtime-bound
variable, a nested function call, a bare `*`, or a `/regex/` literal.

**Runtime lookup, not grammar knowledge**: the grammar has zero built-in
knowledge of what functions exist — `FNAME` is just `/[a-zA-Z_][a-zA-Z0-9_]*/`.
Every function name is resolved against a name-keyed registry
(`ReferenceFunctionFactory`) at transform/build time, not parse time. This is
the central design choice that keeps the grammar flat and the opportunity
to add a custom functions capability when needed.

Reference functions are self-documenting in the same way that match
functions are.

### What functions do

Functions do one of six jobs:
- sets the narrowing context (e.g. a path segment)
- points to a single result (e.g. :index(5) or :first())
- retrieves a field from metadata
- matches on a field from metadata
- retrieves a well-known file (e.g. :errors() retrieves the run results
errors.json file)
- retrieve an arbitrary file from run results by the name the csvpath writer
gave it (e.g. a Parquet file named `invoices.parquet` found in a `name_three`
csvpath instance run home)

We talk about these as:
- pointers (pick one thing)
- context setters (narrow the search scope)
- file accessors (pull the full content of a file)
- field accessors (pull a value from a metadata file)

Note: when a function is used to retrieve the content of a file only one
file may match the reference. For e.g., it is not possible to pull the
contents of all the errors.json files for a run at once. You can identify all
the errors files by pulling the paths to the csvpath statement components of
the run, knowing `errors.json` always has the same name and location for each.
And you can select a subset of those errors JSON files by matching on a
metadata field of one or more errors, resulting in multiple errors.json paths.
But you cannot access the content of more than one errors.json file at once
solely using a reference. The same is true of all file types, not just errors
files.

#### Function arguments
Functions may have zero or one argument. Arguments do one of three things:
- Point
- Narrow
- Match

An argument that enables a function to point provides additional variable
information. For e.g. `:index(5)` is always a pointer but it only works when
it is given the information indicating which index it refers to, in this case
the 0-based `5`, meaning the 6th item.

An argument that narrows enables a context-setting function to know what its
context creating constraint is. E.g. `:having("orders")` is a context setter that
needs the ID of a csvpath statement to enforce its limitation on the results of
`name_one`.

An argument that matches allows a field accessor function to indicate a
limitation on its `name_one` or `name_three` results by requiring the value of
its field to match the argument it receives. Take, for e.g.,
`:errors():error_count(:above(2))`. By itself, `:error_count()` provides
access to a csvpath statement's run instance's manifest field tracking the
number of errors. But `:errors():error_count(:above(2))` is selecting the
path to a run instance's `errors.json` (on query()) and the contents of the
same `errors.json` (on resolve()) but only if there were more than `2` errors
in the run of that csvpath instance.

By contrast to the last example,
`$acme.results.:last().orders:errors(:idchain("add[0]"))` returns the path
to the errors.json of the orders csvpath statement in the last acme run on
query and on resolve returns every error in the list where the first add
function generated an error resulting in an idchain of "add[0]", if any.


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


What a pointer or value resolves to depends on where it sits and how it is used:
- A pointer that uniquely identifies an item (file or directory) when used
  with an argument may also be used without an argument to retrieve the same
  value as a field accessor. E.g. $acme.files.:first():uuid() returns a UUID
  value; whereas, $acme.files.:uuid("ab37-fef3...") returns a path to the item
  without resolving to a more specific value. Likewise :fingerprint().
- In name_one, a pointer resolves to a physical file, a named-paths group
  version, or a run.
- In name_three, a pointer resolves to a well-known metadata *file* (e.g.
  `:errors()`) — unless that pointer's own argument is itself another
  pointer, in which case it resolves to a specific *value* inside that file
  instead (e.g. `:errors(:idchain())`). Same trait, one nesting level
  deeper, not a separate category.

**Note on pointers within file functions:**
References are are as simple as we could make them without giving up value.
They are not intended to give the maximum flexibility in extracting
data. In the example above, `:errors(:idchain(...))`, the resulting value
is one or more error dicts with `idchain` keys matching the given idchain.
We don't allow more than one key to be specified and there's no way to do
boolean predicates beyond what you see. In the usual case, if you need more
specificity than a reference gives it is your job to go beyond the basic
access references give you either programmatically or using reference
expressions (multiple references with set operations; discussed elsewhere).

### At most one pointer per chain, per nesting level

A chain may contain any number of context setters but at most one pointer.
Critically, **a pointer used as another function's argument does not count
toward, or act as, the pointer of the chain it is nested in** — it resolves
that inner function's own internal scope. So `:errors(:idchain("..."))` is
legal (one pointer — `idchain` — at the argument level, one pointer —
`errors` — at the chain's own top level). Conversely, `:last():index(3)`
sitting side by side in the same chain is illegal (two pointers, same
level).

### Why a trailing bare `*` is illegal but bare `:all()` is fine

`*` is a **linguistic fragment** equal to: "any X that Y". It names an
open set X and something Y must follow to complete the sentence. The something
could be more path segments, a function on name_one's chain, or a name_three.
`:all()`, by contrast, is already a **complete instruction**. `:all()` says:
*"get me all of them!"* Nothing needs to follow it.

The two are not otherwise equivalent either (see the EXAMPLE SCENARIO below):
`*` **flattens** every wildcard position in the reference into one pooled
search space that a terminal pointer reduces to a single answer; `:all()`
anywhere in the reference **groups** — it switches the *whole reference* into
a mode where every wildcard position (root_major included) becomes a
dimension of a composite group key, and the terminal function distributes
across the resulting cross-product. Confirmed by a worked example: given
named-file `alpha` (paths `zero.csv` [1 version], `one.csv` [2 versions]) and
named-file `beta` (path `two.csv` [2 versions]):

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


#### Why `*` is disallowed as name_three's body, even though it is legal elsewhere

Settled 2026-08-11. `ResultsReferenceFinder3._name_three_selector()` rejects a
bare `Star3` body outright (`"does not support a bare '*' as name_three's
body -- use :all() instead"`), full stop — even combined with a trailing
function (e.g. `.*:errors()`), unlike name_one, where a mid-path or
function-followed `*` is fine per the rule above. This is not the same
"needs something to complete it" argument — a name_three's `*` here would
already have `:errors()` (or another accessor) following it, so the
sentence-completion problem does not apply.

Note: the distinction between `*`'s flatten and `:all()`'s grouping is only
meaningful where there is more than one axis/position. Name_one is a
`/`-joined, multi-segment path, so a wildcard at one position can coexist
with literal segments at others, and pooling across that wildcarded position
(`*`) is different from grouping by it (`:all()`). Name_three's body is
a single, unstructured identity (a statement name or stringified index).
There is no second position for `*` to wildcard against, so `*` and `:all()`
would be exactly the same: always selecting every instance. Rather than give
the same concept two spellings with zero cases where they would ever differ,
the language keeps one canonical form (`:all()`) and disallows the other.

#### RESULTS' full depth model, and the gap `:home()` fills

RESULTS' template depth has exactly four positions in a 2×2 matrix (how
many levels of nesting a reference targets, crossed with pool-vs-group),
plus one position that turned out to need a fifth, different kind of
function entirely:

| Depth | Pooled (one answer) | Grouped (one per distinct value) |
|---|---|---|
| zero levels (direct children, "no template") | bare pointer (`:last()`/`:first()`/`:index(n)`) | *(nothing to group by — no wildcarded position exists)* |
| exactly one level | `*` | `:all()` |
| any depth | `:flatten()` | `:groups()` |

`*`/`:all()` are peers restricted to exactly one wildcarded segment,
regardless of whether a pointer follows. Because they imply wildcarding a
path segment, they only match when a 1 or more-level template is used.
To match all no-template named-files or named-results use :home(). The
meaning of :home() is essentially the same as :all(), but with the
difference that :home() represents the whole path; whereas, :all()
represents one path segment.

Note that in `csvpaths` there is no path dimension so no depth dimension
to name one.


---

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

- **`reference_transformer_3.py`** — `Reference3Transformer(lark.Transformer)`
  builds the parse tree.

- **`reference_3.py`** — the plain value-object graph the transformer builds,
  with no execution context or filesystem access. This is class is used by
  within the v3 package, but not general callers. Callers outside the v3
  package who need to access a reference's names or to use it in a finder or
  reference expression to make queries use a ReferenceParser.

### `ReferenceParser3` (`csvpath/references/reference_parser_3.py`)
The public interface representing a v3 reference language string. Mainly used
by finders and for direct access to the name parts of a reference string.

### Functions: `Function3` and `ReferenceFunctionFactory`

- **`Function3`** (`csvpath/references/functions/function_3.py`) the base class
for real, behavior-having functions. (Note: `FunctionCall3` is the parse tree
object.)

- **`ReferenceFunctionFactory`** (`reference_function_factory_3.py`) is the
name-keyed registry for all functions. `add_function(cls)` allows for future
custom function registration.

#### Existing functions

For a breakdown of existing functions, see: specs/references_v3/notes/function_coverage_matrix.md

### `ReferenceFinder3` ABC and results containers

- **`ReferenceFinder3`** (`reference_finder_3.py`) is an ABC taking `(*, csvpaths,
ref: ReferenceParser3)`. `query()` is `@abstractmethod` — each datatype's
storage layout differs enough that there's no generic implementation.
`resolve()` and `resolve_from(selection)` are shared (concrete) on the ABC:
`resolve()` = `resolve_from(self.query())`; `resolve_from` accepts either a
`ReferenceResults3` or a `list[str | UUID]` (narrows a fresh `query()` via
`ReferenceResults3.select()`), then calls the abstract `_extract_data()` on
each result to fill in `.data`.

- **`ReferenceResults3`** the container acting as a list of results found by
querying a finder with a reference.

- **`ReferenceResult3`** the container for a specific item found by evaluating
a reference. Reference results have three fields that indicate the item found
when the query function was called, of which one is conditional to specific
datatypes. And one field that optionally contains a resolved value after the
resolve function is called.

| Field | Type | Meaning |
|---|---|---|
| `path` | `str`, required | A file-system path — but its exact *kind* (a directory vs. a file, and if a file, which one) is never recorded on the object itself; it is entirely determined by which finder/branch produced the result. See the "What `path` actually holds" table below. |
| `uuid` | `str \| None` | The matched entity's own registered UUID — `None` when the result is directory-level with no single registered version (e.g. a name_one-terminal FILES query with no version pointer). |
| `identity` | `str \| None` | Which specific *sub-entity*, within `path`+`uuid`. This field covers the identity of `csvpath` statements with `group.csvpaths` and worksheet names within `.xlsx` files |
| `data` | `Any`, mutable | Empty at `query()` time; filled in by `resolve()`/`_extract_data()` afterward, on the same instances — the only mutable field. |

`__eq__` compares all four fields (`path`+`uuid`+`data`+`identity`) — this is
what `ReferenceResults3.deduplicated()` uses to collapse true duplicates.
Different results may be returned after `resolve()` than would after only
`query()`.

**What `path` actually holds** — there is no discriminator field recording
this, so it must be inferred from which finder/branch produced the result:

| Producer | What `path` holds |
|---|---|
| FILES, a version match | the specific version file |
| FILES, name_one-terminal (no version pointer) | the named-file's file-home *directory* |
| CSVPATHS, any version match | the group's `group.csvpath` *file* — always the same path; only `uuid`/`identity` distinguish versions/statements |
| RESULTS, a run-level match | the run's own home *directory* |
| RESULTS, an instance-level match | the instance's own home *directory* (a subdirectory of the run) |
| Rule 1a (bare `'*'`+`:manifest()`, a global ledger — see below) | the ledger file itself, e.g. `.../manifest.json` — `uuid` always `None` |
| Rule 1b (an ordinal pointer riding with the bare global-ledger `:manifest()` — see below) | the *same* ledger file path as Rule 1a, but with a real `uuid` attached to select an entry) |


### The finders
`FilesReferenceFinder3`, `CsvpathsReferenceFinder3`, `ResultsReferenceFinder3`
find results based on a ReferenceParser which represents a reference string.

### Root `:manifest()` and `:definition()` files
All named-things areas have global ledger `manifest.json` files tracking all
add actions (registers, loads, runs). Each named-file, named-paths group, and
named-results run has its own manifest.json, as does each instance in a name-
result.

Named-files and named-paths groups may also have a definition.json file that
holds additional config information controlling how files are registered and
how named-paths groups are run. `definition.json` is common but not mandatory.

Both files may be accessed by references that address all named-things and
use `:manifest()` or `:definition()` without other path info. For e.g.
`$*.files.:manifest():last()` returns the last file registration data
captured in the global files ledger manifest. To get a reference to the
manifest as a whole, simply use `:manifest()` alone.

Definition file references always act on the complete JSON structure, but
can return a single field, if a field accessor is used, or return None if
a field accessor is given an appropriate match value argument. For e.g.
`$acme.files.:description(:on_arrival(:not_none()))`


-----------------------------------


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

### Rule 1 / Rule 1a / Rule 1b — whole-resource content and the global-ledger exceptions

Settled 2026-08-07 (`notes/manifest_field_functions_proposal.md`), extended
in code shortly after. Governs every whole-resource content function
(`:manifest()`, `:definition()`, and the well-known-file content functions
`:errors()`/`:vars()`/`:meta()`/`:data()`/`:unmatched()`/`:file()`) across
all three datatypes.

- **Rule 1 — whole-resource content always resolves to exactly one entity,
  full stop, no exceptions.** These functions never pool raw content across
  more than one named-file version, named-paths group version, run, or
  instance. To reach a Result Instance Manifest you must resolve to one run
  *and* one instance within it — `:all()` at either level, combined with a
  content accessor, is illegal; so is a version-selecting reference matching
  more than one version with no pointer to pick between them, *even* for
  files/csvpaths' own `manifest.json` (a single shared array across every
  version, where reading several matched entries would be comparatively
  cheap) — an earlier draft of this rule carved out an exception for exactly
  that "cheap, already-read, just sliced" case, and David rejected it:
  tying legality to a storage detail (does this entity type happen to keep
  its versions in one shared file, or one file per version) is a leaky
  abstraction — the same syntax could become legal or illegal if a future
  entity type's storage changes. The corrected, adopted rule has no
  carve-outs: reading full content with a reference always touches exactly
  one entity, regardless of how any given entity type happens to persist
  its data today.
- **Rule 1a — the one exception is a real, existing global ledger, and it
  is per-function.** `'*'` (or any other unresolved-entity position) at
  `root_major`, combined with a *bare* `:manifest()`, resolves to that
  datatype's own global ledger instead of raising — because exactly one
  such single resource genuinely exists per datatype (the archive-root
  `manifest.json` for RESULTS, the named-paths loads ledger for CSVPATHS,
  the equivalent for FILES). `:definition()` has no equivalent global
  ledger anywhere in the codebase, so `$*.files.:definition()` (or the
  CSVPATHS/RESULTS equivalent) stays illegal — enforced by the finder
  layer raising, not by the grammar (the grammar stays permissive on
  purpose; see §5's grammar section). Implemented once per finder as an
  early `query()` branch (`_is_bare_pointer_reference(reference,
  "manifest")`, shared on the ABC) that returns the ledger file's own path
  directly via the ABC's shared `_query_well_known_file(home, filename)`
  (same helper `:manifest()`/`:definition()`'s bare, sole-content shape
  already uses at literal `root_major` — see the section above), giving a
  result with `uuid=None`.
- **Rule 1b — an ordinal pointer riding with the bare global-ledger
  `:manifest()` selects one entry out of it by position, instead of
  dumping the whole ledger.** E.g. `$*.results.:last():manifest()` (either
  order — `:manifest():last()` works identically, order-insensitively).
  This is the natural extension of Rule 1a once a pointer joins the same
  bare chain — built during implementation, but **never written back into
  `manifest_field_functions_proposal.md` alongside Rule 1/1a**, only
  documented in code comments (`_pointer_before_manifest()`, shared on the
  ABC — detects a pointer-plus-bare-`:name()` shape in either order;
  `query()`'s own early branch in each finder applies the pointer directly
  against the ledger array, giving a result whose `path` is *still* the
  ledger file's own path, but whose `uuid` is now the selected ledger
  entry's own uuid/run_uuid). `_extract_data()` re-derives the right
  ledger entry from that uuid at resolve time, rather than reading it off
  `result.path` again (since `result.path` is the ledger file, not a
  per-entry resource).

**Why this matters beyond the narrow bare-chain shape**: once `'*'`
traversal supports `:manifest()` combined with real narrowing (`:all()`,
`:flatten()`, a literal prefix — not yet built, see §6/§7), a genuine
traversal result will *also* carry a real, non-`None` uuid — the same
signal Rule 1b's own result carries. `result.uuid is not None` therefore
cannot be used to tell "this came from Rule 1b" apart from "this is a real
traversal result needing its own group/run's own manifest read directly" —
only comparing `result.path` against the ledger's own known, fixed path
can. This is the central blocker for the `:manifest()`+`'*'`-traversal gap
tracked in §6.

Tested by `TestGlobalArchiveLedger`/`TestGlobalArchiveLedgerOrdinalIndexing`
(`test_results_reference_finder_3.py`), `TestGlobalLoadsLedger`/
`TestGlobalLoadsLedgerOrdinalIndexing` (`test_csvpaths_reference_finder_3.py`),
and `TestGlobalArrivalsLedger`/`TestGlobalArrivalsLedgerOrdinalIndexing`
(`test_files_reference_finder_3.py`) — same concept, one differently-named
ledger per datatype.

### `_check_position()` — enforced, declarative position validation

Added 2026-08-14 (`ReferenceFinder3._check_position(function, position,
datatype)`, shared on the ABC), replacing scattered, inconsistent
"is this recognized" guards each finder used to hand-write on its own. The
real bug this closes: a hand-written guard only ever checks for the
*specific* names it happens to know about — anything genuinely unrecognized
silently falls through as a no-op instead of raising. Confirmed live before
this fix, for more than one finder independently: `$acme.csvpaths.:name
("x")` (a FILES-only function, meaningless for CSVPATHS) silently no-opped
rather than raising — `CsvpathsReferenceFinder3._resolve_versions()` had no
guard at all covering this case, while `query()`'s own `name_three` handling
did (for a *different* set of cases), an inconsistency within one finder,
not just across finders.

Each `Function3` subclass now declares `POSITIONS: dict[datatype, tuple[
position, ...]]` — which of `NAME_ONE`/`NAME_TWO`/`NAME_THREE` it is legal
at, per datatype (`Reference3.NAME_ONE`/`NAME_TWO`/`NAME_THREE` are the
three position constants). `_check_position(function, position, datatype)`
raises unless `position in function.POSITIONS.get(datatype, ())`. Rolled
out incrementally, one finder at a time (CSVPATHS first, then FILES, then
RESULTS) — a function with no `POSITIONS` entry for a given datatype has
simply not been migrated to this mechanism by that datatype's own finder
yet, not necessarily illegal everywhere; only a finder that actually calls
`_check_position()` in a given code path enforces it there. By the time
RESULTS was retrofitted (the last of the three), every finder's own
name_one/name_three dispatch called it on every function in the relevant
combined chain, closing the "unrecognized extra silently riding along"
bug class project-wide, not just for the one case that surfaced it.

Tested by `TestPositionEnforcement` in each of `test_csvpaths_reference_finder_3.py`,
`test_files_reference_finder_3.py`, and `test_results_reference_finder_3.py`.

### The manifest field-accessor catalog — Part A/B, and `:path()` (Rule 2)

The big rollout following `notes/manifest_field_functions_proposal.md`'s own
Part A/B tables — **34 field-accessor functions** now live in
`csvpath/references/functions/fields/` (up from zero at the point §5's
"Fourteen concrete functions" table was written), plus `:path()`. This
section describes the *shape* shared by all of them; for the exhaustive
per-function `KEY` mapping, treat `manifest_field_functions_proposal.md`'s
own Part A/B tables as authoritative — they are not reproduced row-for-row
here.

- **Rule 2 — path accessors are exempt from Rule 1 and are always
  poolable.** `:path()` takes any whole-resource content function as its
  argument and returns the filesystem path to that resource instead of its
  content (`:path(:errors())`, `:path(:manifest())`, etc.) — because a path
  is a cheap scalar, not a raw structure, `:path()` calls are allowed to
  pool across `'*'` and across unresolved versions/runs (`$*.results.:path
  (:errors())` returns a list of paths, one per matching instance).
- **Rule 3 — field/key accessors are also exempt from Rule 1 and are
  always poolable**, for the same reason as Rule 2: a single field's value
  (or a small fixed-shape value, e.g. `:file_fingerprints()`'s dict) is
  cheap, not a raw structure to merge. `$*.files.:uuid()` is legal and
  returns a list of uuids, one per version of every matched named-file —
  the cross-product of the entity axis (`'*'`) and the unreduced-within-
  entity version/run axis. This is exactly the case Rule 1 exists to
  prevent for whole-resource *content* — the same cross-product with full
  manifest dicts instead of scalar uuids is the expensive, unwieldy case
  that motivated Rule 1 in the first place.

**Shared shape** (`Function3` subclasses in `functions/fields/`, one file
each): `ROLE = Function3.VALUE`; `DATATYPES` lists which of
FILES/CSVPATHS/RESULTS the function applies to; `SOURCE` is `"manifest"`
(the common case — reads a key straight off whichever manifest entry a
pointer, or the absence of one, already resolved) or `"definition"` (reads
from `definition.json` instead — `:scripts()`/`:webhooks()`/`:transfers()`/
`:destinations()`/`:on_arrival()`/`:sources()`, CSVPATHS/FILES only, no
RESULTS equivalent); `KEY` is a `{datatype: literal_key_path}` dict — one
function can read a *different* literal manifest key per datatype (e.g.
`Uuid3.KEY` reads RESULTS' run-scope `"run_uuid"` field, not a bare
`"uuid"`, since RESULTS' own bare `uuid` field is deprecated/vestigial —
see `RunUuid3` for the always-available name for the same value); `POSITIONS`
(§5, "`_check_position()`") declares which of NAME_ONE/NAME_THREE is legal,
per datatype — RESULTS' own `KEY`/`POSITIONS` commonly carry *two* entries
per function, one for run scope (`Reference3.RESULTS`) and one for instance
scope (`Reference3.RESULT`, singular — a separate scope constant from the
datatype constant `RESULTS`), since the same field name can mean two
different literal keys depending which scope it is read at.

_Extraction_ is generic, not per-function: `_extract_field_value(container,
key_path)` (shared on the ABC) walks a dotted `key_path` (e.g.
`"on_arrival.named_paths_group"`) through whichever dict was already read
(a manifest entry or a `definition.json` dict), returning `None` the moment
any segment is missing — absence is normal, not an error, matching
`definition.json`'s own established optionality. A `definition`-sourced
field additionally needs the *group name*, not a uuid, to call
`describer.get_config(name)` — see the `'*'`-traversal section below for
`_group_manifest_entry()`, the helper this needed once traversal made
`root_major` no longer reliably a literal name.

Representative functions, by rough category (not exhaustive — see the
proposal doc's own tables): identity/provenance (`:uuid()`, `:identity()`,
`:fingerprint()`, `:origin()`, `:origin_data_file()`); timing
(`:time()`, `:time_completed()`); naming (`:named_file_name()`,
`:named_paths_name()`, `:named_results_name()`, `:home()`,
`:named_file_home()`, `:manifest_path()`); RESULTS-run-specific
(`:run_uuid()`, `:hostname()`, `:username()`, `:status()`, `:valid()`,
`:completed()`, `:files_complete()`, `:mark()`, `:method()`, `:serial()`);
RESULTS-instance-specific (`:preceding_instance_identity()`,
`:source_mode_preceding()`, `:actual_data_file()`); counts/collections
(`:named_paths_count()`, `:named_paths_identities()`,
`:file_fingerprints()`); `definition.json`-backed (`:scripts()`,
`:webhooks()`, `:transfers()`, `:destinations()`, `:on_arrival()`,
`:sources()`).

Tested by `tests/references/functions/` (one test file per function) plus
each finder's own `TestFieldAccessorFunctions` class, and (FILES/CSVPATHS
only, no RESULTS equivalent) `TestDefinitionFieldAccessorFunctions` — real-
file round trips, not just fakes, for the run/instance-scope shared-key
cases in particular.

### `:having()` and `:from()`/`:to()` ranges

`:having("identity")` (CSVPATHS only) filters the version list down to
versions whose own `named_paths_identities` actually contains that
identity, *before* any pointer reduces further — `:having("orders"):last()`
means "the last version that actually has an `orders` statement." Combined
with no pointer, lists every matching version unreduced (same "no pointer,
no reduction" convention every other context-setter follows). **Not yet
built for RESULTS** — logged as a real, wanted follow-up (`specs/
references_v3/spec/references_expressions.md`): "give me all the runs
where the named-paths group included a csvpath with identity X" needs
`:having()` mirrored onto RESULTS, filtering by whether a run's matched
statement has a given identity, the RESULTS-side analog of the CSVPATHS
version filter.

`:from()`/`:to()` — a named-paths group's own load time, and a RESULTS
run's own arrival time, are both real arrival-date concepts ("our version
of BETWEEN in SQL or `range()` in Python" — `:to()` is inclusive of its own
position/date). Built at two different levels, with different mode
support at each:

- **Version/run-level** (CSVPATHS name_one; RESULTS run level) — **two
  independent modes**, picked by each bound's own value type: index-mode
  (`int`/`:index(n)`) positionally slices the (possibly `:having()`-
  filtered) version/run list; date-mode (`str`/`:date(...)`) filters by
  each entry's own `"time"` field instead — comparing *positions* would be
  meaningless for a date bound, so the two modes use genuinely different
  application logic, not just different parsing. Mixing modes in one
  `:from()`/`:to()` pair is rejected — not because it is meaningless (e.g.
  `:from(:date("2025-01-01")):to(:index(10))`, "10 versions/runs starting
  from this date," is a reasonable ask), but because it is *ambiguous* and
  deliberately left unsettled which of at least two readings is meant — is
  the index bound an absolute position in the full list, or relative to
  wherever the date bound starts matching? At most one pointer, riding
  alongside `:from()`/`:to()` in the same chain, reduces the *range* to
  one, not the full candidate set.
- **Statement level** (CSVPATHS name_three; RESULTS name_three) —
  **index-mode only**, no date mode: an individual statement/instance has
  no arrival time of its own, only the version/run it belongs to does.
  CSVPATHS' statement-level range additionally has no per-statement uuid
  at all (only the whole group version has one) — a range's several
  matched statements all share identical `path`/`uuid`, so
  `ReferenceResult3.identity` (added for exactly this, see the "four
  fields" note earlier in §5) is what `_extract_data()` uses to tell them
  apart, not `name_three.body` (only ever set for the single-literal-
  identity shape). RESULTS' statement-level range combined with a content
  accessor is count-*dependent*, not a blanket rejection the way `:all()`
  combined with a content accessor is — mirrors the run-level "more than
  one candidate needs a pointer" rule exactly: a range that happens to
  narrow to exactly one statement in a given run is fine with an accessor,
  same as a pointer narrowing a candidate list to one already is.

Tested by `TestHaving`/`TestVersionRange`/`TestNameThreeRange`
(`test_csvpaths_reference_finder_3.py`) and `TestRunLevelRange`/
`TestRunLevelDateRange`/`TestStatementLevelRange`
(`test_results_reference_finder_3.py`).

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

### `ReferenceExpression3` — UNION/SUBTRACT/INTERSECT over references

Settled and built 2026-08-18/19 (`specs/references_v3/spec/
references_expressions.md` is the full design record; this section states
only the settled result). Motivation: a single reference can't answer
cross-datatype questions like "find all the named-files used in runs where
the named-paths group was updated yesterday" — that needs a set operation
across a RESULTS query and a CSVPATHS query. `ReferenceExpression3.__init__
(*, left, op, right, csvpaths)` — `left`/`right` are each a non-empty
reference `str` or another `ReferenceExpression3` (sub-expressions nest
freely); `op` is one of the class-level constants `UNION`/`SUBTRACT`/
`INTERSECT`. Works internally through `.resolve()` only — there is no
meaningful `.query()`-only mode, since `INTERSECT`/`SUBTRACT`'s join key
*is* resolved field-accessor data (see below), not something query-time
path/uuid alone can express. Two small pieces built first, as reusable
building blocks:

- **`ReferenceFinderFactory3.for_reference(*, reference, csvpaths)`**
  (`reference_finder_factory_3.py`) — parses a raw reference string and
  dispatches to the correct one of the three finders based on the parsed
  `Reference3.datatype`. Nothing before this auto-routed a string to the
  right finder; every test had hand-picked one directly.
- **`ReferenceResults3.deduplicated()`** (§5, "four fields" note) —
  collapses duplicates by `ReferenceResult3`'s own full `__eq__`
  (`path`+`uuid`+`data`+`identity`), first-occurrence-wins, order
  preserved.

**The core design tension**: `ReferenceResult3.path`/`.uuid` mean
different things per datatype (a `group.csvpath` file vs. a run directory)
and are not comparable across them — so the join key for `INTERSECT`/
`SUBTRACT` cannot be path/uuid. The join key is instead **whatever scalar a
side's own trailing field accessor resolves to** (`.data`, after
`resolve()` — `:identity()`, `:named_paths_name()`, `:uuid()`, `:time()`,
etc.). A side whose reference does not end in a scalar-valued accessor (or
resolves to a list/dict, e.g. `:named_paths_identities()`,
`:file_fingerprints()`, `:scripts()`) is not usable this way; `_hashable()`
raises `ReferenceException3` clearly rather than failing deep in a set/dict
implementation if an unhashable value is encountered. `None`-valued keys
never match anything, on either side.

- **`UNION`** does not use the join key at all — pure concatenation of both
  sides' own native results, then `.deduplicated()`. No filtering, no row
  multiplication. If a caller wants to see which items *pair* with which,
  that is done *after* the union, by comparing `.data` across the merged
  results — there is no separate "enumerate matching pairs" operation
  needed; `UNION` already covers that need if the caller wants it.
- **`INTERSECT`/`SUBTRACT`** are filters, not joins that multiply rows.
  Only the **right** side is reduced to a plain `set` of resolved keys
  (which right-hand item carried a given key never matters — right-hand
  items never appear in the output). The **left** side is deduplicated
  only by full item equality (`.deduplicated()`) — *never* collapsed by
  key — then each surviving left item individually survives (`INTERSECT`)
  or is removed (`SUBTRACT`) based on whether its own key exists anywhere
  in the right side's key set.

**A real bug caught by testing against a concrete worked example, not by
design review**: an early draft collapsed the *left* side to one item per
distinct key before filtering too, mirroring the right side — correct for
"one result per identity," silently wrong for "give me every run where the
group had an `orders` statement," which needs every matching run, not one
exemplar per group. Caught via a direct repro (two named-paths groups, one
with 2 runs, one with 3, both matching `orders` → only 2 results came back
instead of 5) before shipping, then verified end-to-end against the exact
worked numbers in `references_expressions.md`'s own canonical example: 7/6/5
`ReferenceResults` for the `UNION` variants (both groups matching / one
group deleted / neither group's *current* version matching), 5/2/0 for the
equivalent `INTERSECT` variants.

Tested by `test_reference_finder_factory_3.py`, `test_reference_results_3.py`
(`.deduplicated()`), and `test_reference_expression_3.py` (pure operation-
logic tests against synthetic `ReferenceResults3`, constructor validation,
and a full end-to-end "orders" scenario with real on-disk RESULTS/CSVPATHS
fixtures reproducing the worked numbers above exactly).

### `'*'` traversal, fully generalized — field accessors, `:having()`/`:flatten()`/`:all()`, path narrowing, `name_three`, and pointer optionality

`_query_star_traversal()` (each finder) handles `root_major == '*'` —
"every named-file"/"every named-paths group"/"every named-results group" —
once Rule 1a/1b's own narrow bare-chain shapes (above) don't already claim
the reference. Originally built narrowly (RESULTS: a bare pointer only,
zero-level; CSVPATHS: a bare pointer or `:all()`, no field accessors, no
`:having()`) and generalized across several passes, driven directly by
`ReferenceExpression3`'s own needs — cross-datatype set operations are
exactly the case where "search every group/run without already knowing
candidate names" stops being optional.

- **A run/version-level field accessor may now ride alongside the pointer**
  (e.g. `$*.results.:last():uuid()`, `$*.csvpaths.:all():named_paths_name()`).
  For RESULTS this needed no new machinery — `_results_for_run()` already
  builds each candidate's `ReferenceResult3` from its own real run
  directory, independent of any group-name context. CSVPATHS needed a real
  fix: field-accessor resolution reads a matched version's own manifest
  entry via `get_manifest_for_name(root_major)`, which breaks when
  `root_major` is the `'*'` token (no group is literally named `"*"`) —
  `_group_manifest_entry(root_major, uuid)` (`csvpaths_reference_finder_3.py`)
  searches every named-paths group's manifest for the matching uuid when
  `root_major` is `'*'` (uuids assumed globally unique, an assumption
  already made elsewhere in this codebase), returning `(group_name, entry)`
  — used for both manifest-sourced fields and `definition.json`-backed
  ones, which need the group *name* for `describer.get_config(name)`.
- **`:having()` (CSVPATHS) and `:flatten()` (RESULTS) are now recognized in
  traversal.** `:having()` filters each group's own manifest before either
  mode's reduction, the same position it occupies at the literal-root
  level — closing a real, previously-latent bug in the same pass, not just
  adding a feature: `:having()` was never checked for at all in
  `_query_star_traversal()` before this, neither rejected as unsupported
  nor applied, so it was silently *dropped* (`$*.csvpaths.:all():having
  ('orders')` returned every group's every version, unfiltered). `:flatten
  ()` pools every group's runs at any depth before the pointer reduces —
  `_discover_run_homes(None)` already discovers across every group with no
  depth restriction of its own, so this needed only routing to it instead
  of the zero-level-filtered candidate set.
- **`:all()`'s own meaning-collision, resolved by a direct worked
  example.** RESULTS' `:all()` already has two settled, non-conflicting
  meanings depending on position — at `name_three`, "every instance within
  one already-selected run"; at a literal-root `name_one`, "exactly one
  level of template wildcarding, grouped by the observed value at that
  position." Neither says what `:all()` should mean at `name_one` when
  `root_major` is *also* `'*'` — both "which group" and "which template
  value" are open at once, and naively extending either existing meaning
  alone gives a silently wrong answer (pooling by template value alone
  conflates two different groups that happen to reuse a subfolder name;
  grouping by group alone loses the template distinction within a group).
  Resolved via a worked example in `normative_reference_examples.txt`
  ("THE `:all()` MEANING COLLISION AT STAR TRAVERSAL" — two groups, one
  template value deliberately reused by both, three candidate
  interpretations spelled out with exact result counts: 2, 2, 3) —
  partition by the **composite** `(group, template-value)` key, matching
  `FilesReferenceFinder3`'s own already-built `:all()` star-traversal
  precedent exactly (there, `file_home` already embeds the named-file's
  own name as a path prefix, so partitioning by `file_home` already *is* a
  composite key).
- **Literal/`'*'` path narrowing and `name_three` are now supported.**
  Both turned out to be mechanical generalizations of building blocks the
  work above already required, not new design questions:
  `_compile_path_pattern()`/`_matches_prefix()`/`_matches_prefix_at_least()`/
  `_group_key()` are shared helpers already built for the literal-root
  case, applied per-candidate's-own-group-home instead of one fixed home
  (the same trick already used for the zero-level bare pointer, `:flatten
  ()`, and `:all()`); `_results_for_run()` already does the identity/
  `:all()`/range selection entirely from a real run directory, independent
  of group. The one real design point, not just wiring: `:all()` grouping
  can select more than one run overall (one per partition), so a
  `name_three` *content* accessor is rejected there — mirrors the literal-
  root case's own restriction — while a `name_three` *field* accessor is
  explicitly allowed and poolable (confirmed against the already-shipped
  literal-root precedent before building this: `":all():last().invoices
  :uuid()"` already resolves fine there, one result per matched run — so
  `"$*.results.:all():last().invoices:uuid()"` can return a list of zero
  or more uuids, one per matched run that actually has that identity, not
  multiplied further).
- **A pointer is now optional in every traversal shape, for both RESULTS
  and CSVPATHS.** Absence means every matched candidate comes back,
  unreduced — the same meaning a missing pointer already has at every
  literal-root shape. This was investigated deliberately, not assumed,
  before being built: `FilesReferenceFinder3`'s own `'*'` traversal never
  requires a pointer, in any of its four modes (a missing pointer returns
  a deduped list of distinct `file_home` values); RESULTS' own literal-
  root `query()` never requires one either. Both fixed to match.
  `CsvpathsReferenceFinder3`'s traversal is the actual **outlier**, not
  the precedent it first appeared to be while building the `:having()`/
  `:flatten()` work above: it requires a pointer in POOL/flatten mode,
  optional only in GROUP/`:all()` mode — left as-is deliberately, a known,
  documented, not-silently-fixed inconsistency, not blocking anything
  built so far. Removing the old unconditional "requires a pointer" check
  surfaced a *second*, previously-latent bug each time, for a related but
  distinct reason each time: for RESULTS, `_extract_data()`'s star-
  traversal branch had checked `isinstance(root_major, Star3)`
  unconditionally (fixed to also require `has_manifest`, since a bare-
  pointer `resolve()` with neither `:manifest()` nor a field accessor had
  been incorrectly taking the global-ledger-by-uuid path instead of
  falling through to "no single unambiguous payload → `None`"); for
  CSVPATHS, the "is this combination supported" check had been a
  *blacklist* (only rejected `:manifest()`/`:from()`/`:to()` by name), so
  `:definition()` (and any other genuinely unrecognized function) silently
  passed through unrejected once the mandatory-pointer rule stopped
  masking it — fixed by switching to the same whitelist pattern (enumerate
  what's legal, reject everything else) already used elsewhere.
- **`:groups()`, literal/`'*'`-prefixed `:having()`/`:flatten()`
  combinations beyond what's listed above, and `:manifest()` combined with
  real narrowing all stay unsupported in traversal** — see §6/§7.

Tested by `TestStarTraversal*`/`TestGroupManifestEntry` classes across
`test_results_reference_finder_3.py` and `test_csvpaths_reference_finder_3.py`,
plus `TestStarTraversalPlusFieldAccessorNowWorks`/
`TestHavingAndFlattenPlusStarTraversalNowWork` in `test_reference_expression_3.py`
(the same integration point `ReferenceExpression3` actually needs — a plain
reference *string* with `root_major='*'` resolving successfully all the way
through `ReferenceFinderFactory3` → the finder → `resolve()`, not just when
hand-built directly against a finder class).

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
  reference expressions in two of its example queries. This section used
  to describe that as aspirational, since NOT/UNION/INTERSECT-combining
  was explicit "later phase" work — **resolved 2026-08-18/19: `Reference
  Expression3` is now built** (`UNION`/`SUBTRACT`/`INTERSECT`, no `NOT`)
  — see §5, "`ReferenceExpression3`."
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
- **`:manifest()` combined with real `'*'`-traversal narrowing is still
  unsupported**, in both `ResultsReferenceFinder3` and
  `CsvpathsReferenceFinder3` — the one traversal restriction that has
  survived every generalization pass described in §5's `'*'`-traversal
  section. Not just unbuilt: `_extract_data()` cannot yet reliably tell a
  Rule-1b global-ledger result apart from a genuine traversal-selected
  result once both can carry a real uuid (see "Rule 1 / Rule 1a / Rule
  1b," §5) — comparing `result.path` against the ledger's own known,
  fixed path (rather than the `result.uuid is not None` check both
  finders currently lean on) is the identified fix, not yet implemented.
  Also needs the same "grouping can select more than one result, so a
  whole-resource content function needs the single-entity guard" treatment
  already applied to `name_three` content accessors in the same section.
  Planned as a dedicated next branch.

---

## 7. Not yet built at all

**Everything this section originally tracked as unbuilt is now built** —
`CsvpathsReferenceFinder3` and `ResultsReferenceFinder3` (§5), `root_major
== "*"` traversal for all three datatypes including the full flatten-vs-
group cross-product behavior (§5, "`'*'` traversal, fully generalized"),
`ReferenceExpression3` (§5), and the great majority of the functions this
section used to list as missing (`:date()`, `:time()`, `:uuid()`,
`:from()`/`:to()`, and the whole field-accessor catalog — §5). The design
reasoning behind each of those (why csvpaths/results needed genuinely
different finder logic than files, why results' run-ordering couldn't just
reuse the archive-wide global manifest, etc.) is preserved in §5's own
narrative rather than repeated here.

**Still genuinely not built:**

- **`:before()`/`:after()`, `:yesterday()`, `:quarter()`, `:regex()`,
  `:choice()`, `:names()`, `:message()`, `:count()`, `:above()`,
  `:has_errors()`, `:type()`, `:at()`** — appear in the spec/example-
  queries docs but have no `Function3` subclass yet. `:having()` is also
  not yet built for RESULTS specifically (§5, "`:having()` and `:from()`/
  `:to()` ranges") — a real, wanted follow-up, not merely aspirational.
- **`:manifest()` combined with real `'*'`-traversal narrowing** — §6.
- **`:groups()` combined with `'*'` traversal**, and literal/`'*'`-prefixed
  `:having()`/`:flatten()` combinations beyond what §5 already lists — no
  established per-GROUP-of-named-\[paths/results\]-groups meaning has been
  settled for the deep/any-depth case yet; left for if/when a real use
  case asks, same as `:groups()`'s own deferred status at the literal-root
  level once was before it was eventually built there.
- **Type-ahead** — a prototype exists (`specs/references_v3/notes/
  autocomplete_prototype.py`) demonstrating the intended mechanism: Lark's
  `parse_interactive()`/`InteractiveParser.choices()` against actual LALR
  parser state, layered with a function registry filtered by datatype and
  slot (name_one path-slot vs. name_three part-slot) — deliberately in
  place of v1/v2's hand-maintained follow-set lists. It predates the
  grammar that actually got merged (written against a draft
  `reference_v3.lark` with different terminal names) and is not wired into
  the real grammar or `Function3`/`describe()` metadata at all.
  `REFERENCE_GRAMMAR_3` has been separately confirmed to work under
  `parser="lalr"` (a prerequisite for this technique), but no
  `parse_interactive()`-based code exists in `csvpath/references/` itself
  yet.
- **`{...}` interpolation evaluation** — parsing/validation is built (see
  §5), but actually resolving an `InterpolatedString3` into its final text
  is not. Needs two prerequisites: variable resolution (looking up an
  `@name` against a real `CsvPaths`/scope context — not built), and at
  least one real `VALUE`-role function usable inside `{...}` for something
  other than a bare field lookup (e.g. a future `:year()`) — many
  `VALUE`-role functions exist today (the whole field-accessor catalog,
  §5), so the second prerequisite is arguably already partly met; nothing
  currently wires interpolation evaluation up to actually call one at
  runtime.
- **v3 is still not wired into production.** The live managers
  (`results_manager.py`, `file_manager.py`) still dispatch through the
  older v2 reference system (`csvpath/util/references/`) — confirmed by
  grep: only v2's `ReferenceParser`/`Reference` classes are actually
  instantiated in manager code; v3's classes are referenced only in
  comments there. Everything in this document has been built and tested
  self-contained, independent of that integration question.
