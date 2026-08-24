# CsvPath References v3 — Compendium

This document defines the References v3 subsystem, incorporating the
following docs by reference:
- requirements_for_functions.md
- references_expressions.md
- normative_reference_examples.txt
- normative_reference_expressions_examples.txt

No one doc controls. If there is a discrepency, lack of clarity, or
logical question mark, the resolution is to raise the issue to David's
attention for triage and a specification update.

Other non-normative, informational sources to read for background and
dev history include:
- `specs/references_v3/notes/rc_roadmap.md — path to production
- `specs/references_v3/notes/deferred_work_bucket_list.md` — running task list
- `specs/references_v3/notes/ — older text notes
- `csvpath/references` — code comments

Development must include the production of running notes and code
comments documenting each decision made and referencing tests where a
test might be illuminating. Any defered decisions or deferred
implementation must be itemized specifically in the bucket list.

---

## 1. What are References v3?

CsvPath Framework includes a CsvPath Reference Language that provides flexible
general access to the Framework's physical data and metadata model. This
language enables users to ask questions in a declarative syntax rather than
requiring them to programmatically work within the Framework's objects interface.

The expectation is that references will be:
- Easier to use than remembering how to use numerous classes
- More flexible in terms of questions that can be answered practically
- More resiliant and safer in the face of user error
- Less brittle than adding dozens of new methods supporting new querying and reasoning tools
- More understandable when logged by an AI as it iterates through its work

References give access to CsvPath Framework data stores. There are three data
stores each holding a kind of named thing:
- **named-files** — versioned sets of registered data files, with each version having a cryptographic identity
- **named-paths groups** — versioned sets of CsvPath statements that are used as a single entity
- **named-results** — sets of run outputs from applying a named-paths group to a named-file

CsvPath already has two prior versions of CsvPath Reference Language:

- **v1** set the current `$`-prefixed path/name syntax users see everywhere
  (e.g. `$myfile.files.abc`).
- **v2** updated the parsing/resolving implementation behind that same
  syntax (`csvpath/util/references/`: `ReferenceParser`, `FilesReferenceFinder2`,
  `ResultsReferenceFinder2`, `reference_transformer.py`, etc., ~2500 lines).

**v3 is a from-scratch replacement**, motivated by two things:
- v1 and v2 have real tech debt and lack conceptual clarity
- The vision of a more robust reference language giving an AI assistant
a single, concise, general-purpose exploration tool for digging into CsvPath
Framework project states, instead of requiring many narrow, brittle,
purpose-built tools.

v3 is AI-facing only, for now. v1/v2 stay exactly where they are, untouched,
and remain what end users see (identifying runs, registrations, named-paths
loads). v3 lives in a new location, `csvpath/references/`, and follows v1/v2's
naming convention: `_3.py` files, `3`-suffixed class names (`ReferenceParser3`).
v3 tests live in `tests/references/`.

v3 covers only named-file, named-paths-group, and named-results storage. It
does not cover the four runtime datatypes (variables, headers, csvpath match
state, metadata) used as primary CsvPath Validation Language productions and
in `print()` and `error()` statements. Those will be addressed in a follow-on
release post v3's launch.

---

## 2. Overall usage pattern

A reference is a string that is interpreted as a query that gives access to
file paths, identifiers, and metadata field values, as described below.

#### 2.1
The steps to using a reference are:
1. Parse a reference string into a reference object
2. Create a finder that will interpret the reference
3. Register any required variables with the finder
4. Use the finder's query() method to get a list of paths+UUID matching the reference
5. If needed, use the finder's resolve() method to get a file's contents or the values of one or more metadata fields

#### 2.2
References may be used within a lightweight expression language (also
considered part of CsvPath Reference Language) that enables the user to
structure set operations on references. These reference expressions set
operations are:
- UNION
- INTERSECT
- SUBTRACT

#### 2.3
There are a few requirements below, but most reference expressions
requirements are in `specs/references_v3/spec/references_v3_expressions.md`

---

## 3. The reference syntax model

#### 3.1
See `csvpath/references/reference_grammar_3.py` for the formal CsvPath
Reference Language v3 grammar. The reference expressions set operations are
a layer on top of the references grammar.

#### 3.2
Like v1 and v2, a v3 reference is a `$`-prefixed, dot-separated string:

```
$root_major.datatype.name_one[#name_two][.name_three]
```

#### 3.3
`name_one` may carry a `#name_two` worksheet marker (files datatype only, for
XLSX files).

| Segment | Required? | Meaning |
|---|---|---|
| `root_major` | yes | The named object — a named-file name, named-paths group name, or named-results name. |
| `datatype` | yes | One of `files`, `csvpaths`, `results`. |
| `name_one` | yes | See below — meaning differs sharply by datatype. |
| `name_two` | optional, files only | An XLSX worksheet identifier, written as `#worksheet_name` appended directly to name_one's path. |
| `name_three` | optional (for every datatype, per the current spec) | A more specific part of what name_one identified. |

The names `root_major`/`name_one`/`name_two`/`name_three` are inherited from
v1/v2's naming and are kept for continuity and because they make sense in
context even if they aren't obvious names. v1/v2 also allows for a
`name_four` based on a separator, `#`, same as used to create name_two.
`name_four` has few use cases, is rarely used, and is only applicable to the
runtime datatype `variables`. It does not make an appearance in v3.

### `root_major`

#### 3.4
`root_major` is the name of a named-file, named-paths group, or named-results.
It can take a wildcard as explained below. The datatype is a static field
indicating which type of named-thing root_major refers to, one of `files`,
`csvpaths`, or `results`.

#### 3.5
`root_major` can be a static string, a regex (wrapped in `/` chars) or `*`. As discussed further below, `*`
means any existing named-thing.

### The name_one datatype distinction

`name_one` means structurally different things per datatype. The larger
difference is between `csvpaths` and the other two.

#### 3.6
- **`files` and `results`**: name_one is a path-like prefix search. It is
  built from `/`-separated segments. A segment is:
  - a literal name
  - `*`
  - a `:name("...")` function that may include a `.` char which would
    otherwise be illegal.

#### 3.7
  Note that a regex in root_major can stand alone, but in name one and name
  three the `:regex()` function must be used.

#### 3.8
  Segments identify *which logical file* (files) or *which run* (results) —
  a location in a directory tree, matched by prefix. Note that a prefix can
  `''`, i.e. no prefix. This is the case when no template is used during
  file registration or when a run is triggered. Using templates is an optional
  tool for semantically organizing files. If no template is used registrations
  and runs are found directly under their name's home directory. We speak of
  1-level templates, 2-level templates, etc. to describe how many path
  segments the template adds to the path to the home directory.

#### 3.9
- **`csvpaths`**: name_one is a version-selecting expression, not a path.
  A named-paths group has exactly one `group.csvpath` file on disk, updated
  in place every time statements are (re)loaded; there is no per-version
  physical file. Versioning instead lives entirely in the group's own
  `manifest.json`, as an array of load events. So for csvpaths, name_one is a
  time/index/ordinal/UUID expression that selects one or more *entries in
  that manifest array* — every result shares the same `group.csvpath` path,
  differentiated only by UUID (the manifest entry's identifying UUID).

This is why the structure table (below) lists name_one's per-datatype meaning
so differently.

### The role of functions

#### 3.10
Note: high level requirements for functions begin in
`specs/references_v3/spec/requirements_for_functions.md`

#### 3.11
Functions look like `:name_of_function()` and can take 0 or 1 argument, which
is a string, number, function, or regex string wrapped in forward slashes,
like: `/.../`.

There is more information on functions below in their own section.

### The role of variables

#### 3.12
Prior to query, a reference finder can be given variables that may be used in
references. A variable can be any Python object, but the variable value will
be put into a string context so its __str__ must make sense for the reference.

Variable syntax is `@` name, as in `@myvariable`.

Variable support, including registration, is a required, must-have
capability for RC — not optional or deferrable. This specification does
not mandate a particular registration mechanism or user-level interface
for it, but the capability itself must exist before v3 can be considered
feature-complete.

### root_major, name_one, name_three

#### 3.13
- **root_major**: limited only by an exact name, `*` (all named-things), or a
  regex string wrapped in forward slashes, like: `/.../`.
#### 3.14
- **name_one**: limited primarily by constructing the path (literal segments,
  `*`, `:name(...)`), but also by date, index, UUID, and other functions.
  Note that dates here are always evaluated as:
  - for `files`: date of arrival
  - for `csvpaths`: date of load
  - or for `results`: date of run
#### 3.15
- **name_three**: an identifier that combines with name_one to reach specific
  run-result files or values, as in:
  - for `files`: a specific cryptographically identified version of a file
  - for `csvpaths`: a csvpath statement contained in a named-paths group
  - or for `results`: the specific results of running a csvpath statement
    contained in the named-paths group that was used in the run; i.e. a
    component result of the total set of run results.

#### 3.16
Functions in name three can:
  - retrieve files (e.g. `:errors()`)
  - match a specific metadata value to select a file path (e.g.
    `:errors(:idchain("add[0]string[2]"))`)
  - retrieve a specific metadata field (e.g. `:uuid()`)

### Structure breakdown table

#### 3.17
| Datatype | name_one | name_two | name_three (optional) | name_one returns | name_three returns |
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

#### `results`'s full depth model, and the gap `:home()` fills

#### 3.18
`results`' template depth has exactly four positions in a 2×2 matrix (how
many levels of nesting a reference targets, crossed with pool-vs-group),
plus one position that turned out to need a fifth, different kind of
function entirely:

| Depth | Pooled (one answer) | Grouped (one per distinct value) |
|---|---|---|
| zero levels (direct children, "no template") | bare pointer (`:last()`/`:first()`/`:index(n)`) | *(nothing to group by — no wildcarded position exists)* |
| exactly one level | `*` | `:all()` |
| any depth | `:flatten()` | `:groups()` |

#### 3.19
`*`/`:all()` are peers. Both are restricted to one wildcarded segment,
regardless of whether a pointer follows. Because they imply wildcarding a
path segment, they only match when a 1 or more-level template is used.
To match all no-template named-files or named-results use :home(). The
meaning of :home() is essentially the same as :all(), but with the
difference that :home() represents the whole path; whereas, :all()
represents one path segment.

Note that in `csvpaths` there is no path dimension so no depth dimension
to name one.


### A trailing bare `*` is illegal, but bare `:all()` is fine

#### 3.20
`*` is a **linguistic fragment** equal to: "any X that Y". It names an
open set X and something Y must follow to complete the sentence. The something
could be more path segments, a function on name_one's chain, or a name_three.
`:all()`, by contrast, is already a **complete instruction**. `:all()` says:
*"get me all of them!"* Nothing needs to follow it.

#### 3.21
The two are not otherwise equivalent either (see the EXAMPLE SCENARIO below):
`*` flattens every wildcard position in the reference into one pooled
search space that a terminal pointer reduces to a single answer; `:all()`
anywhere in the reference groups. It switches the *whole reference* into
a mode where every wildcard position (root_major included) becomes a
dimension of a composite group key, and the terminal function distributes
across the resulting cross-product. Confirmed by a worked example: given
named-file `alpha` (paths `zero.csv` [1 version], `one.csv` [2 versions]) and
named-file `beta` (path `two.csv` [2 versions]):

#### 3.22
- `$*.files.*.:last()` → 1 result (single most-recent file across everything —
  flattened).
- `$*.files.:all().:last()` → 3 results, one per (named-file, path) pair —
  grouped.
- `$alpha.files.*.:last()` → 1 result (root already literal, so nothing extra
  to flatten across, but still one pooled answer across alpha's paths).
- `$alpha.files.:all().:last()` → 2 results, one per path within alpha.

#### 3.23
A related side finding baked into the same example: `:last()` means
*arrival/registration order* (manifest array order), **not** lexicographic
order on the version filename — version names are content hashes with no
inherent temporal order.

#### Why `*` is disallowed as name_three's body, even though it is legal elsewhere

#### 3.24
`ResultsReferenceFinder3._name_three_selector()` rejects a bare `Star3` body
outright (`"does not support a bare '*' as name_three's body. Use :all()
instead"`), full stop — even combined with a trailing function (e.g.
`.*:errors()`), unlike name_one, where a mid-path or function-followed `*`
is fine per the rule above. This is not the same "needs something to
complete it" argument — a name_three's `*` here would already have
`:errors()` (or another accessor) following it, so the sentence-completion
problem does not apply.

#### 3.25
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

---

## 4. Query vs. Resolve

v3, like v2, splits reference-following into two phases, but the phases mean
something different in v3.

#### 4.1
**Query**: runs the reference as a search and returns 0-or-more results. Each
is the set of:
- a file-system path
- a UUID
- a name two (Excel files only, and optionally)
- an instance ID (`csvpaths` only, and optionally)

#### 4.2
These results always point to a file system location, with the identifiers
needed for any internal file pointer (for Excel and `group.csvpaths`). This
is the case even when the reference is clearly pointing to a metadata field
within that context. In the query stage, a user can trim the list of results
according to path, UUID, etc. without accessing whole files. In some cases
a reference expression may combine two references, when both sets of results
are comparable without further resolution.

#### 4.3
**Resolve**: pulls actual content a reference points to. When a reference
points to a file, resolving returns either bytes (if the reference is to a
binary file, such as an `.xlsx`) or a JSON structure. When a reference
points to a field the return is a string, int, date, UUID, etc.

#### 4.4
It is possible for resolve to return no answer (`None`). A bare results
reference with no metadata pointer has no single well-defined resolve output
of a run; only the path to the run is indicated and that is available in the
query stage.

### Query, by termination point

#### 4.5
A Query terminating at name_one (regardless of any pointer function) is primarily a path,
which may be resolved to a value, if further resolution of the reference is possible.

#### 4.6
| Datatype | What name_one-terminated query() returns |
|---|---|
| files | path to the named-file's file-home directory (directory of version files) |
| csvpaths | path to the `group.csvpath` file |
| results | path to the run directory |

#### 4.7
A query terminating at name_three:

| Datatype | What name_three-terminated query() returns |
|---|---|
| files | path to the specific version file |
| csvpaths | path to the `group.csvpath` file (same path as always; the combined version UUID and statement ID differ) |
| results | path to the specific statement's instance directory within the run dir |

### Resolve — the three-way classification

#### 4.8
A reference resolves to a 0 or more set of one of three kinds of thing:

#### 4.9
1. **First-party registered data** — the actual underlying content — returned
   when no function names metadata at all (e.g. a plain files reference with a
   version pointer resolves to that version file's raw bytes).
#### 4.10
2. **A whole results metadata or data file** — returned when a function names
   a known metadata file (`:errors()`, `:vars()`, `:meta()`, or an arbitrarily-
   named file via `:file(...)`) with no further drilling into it.
#### 4.11
3. **A manifest.json or definition.json file** — file contents of one of the two
   main config files. Note all datatypes have `manifest.json` but only `files`
   and `csvpath` have `definition.json`.
#### 4.12
4. **One metadata field** — returned when config file function or run metadata
   file function itself takes another pointer as its argument, extracting one
   value rather than the whole file (e.g. `:errors(:idchain())`).

Note that a file accessor that takes a field accessor is doing one of two things:
#### 4.13
- if the field accessor has no argument it returns the field's value
#### 4.14
- if the field has an argument, it limits the reference's match to files that
contain fields with exactly that value.

#### 4.15
In the latter case, the resolved reference returns the file, not the field,
because the field is just a predicate, not a retrieval. It is not possible
to pass multiple limiting field values to a reference as a way to be more
discriminating. This is an intentional simplification. Reference expressions
offer one approach to further narrowing.

The full resolve matrix by termination point and pointer kind:

#### 4.16
| | name_one, no pointer | name_three, no pointer | name_one, file pointer | name_three, file pointer | name_one, field pointer | name_three, field pointer |
|---|---|---|---|---|---|---|
| **files** | no default → `None` | version file bytes (name_three always points) | contents of `manifest.json`/`definition.json` | version file bytes | field from `manifest.json`/`definition.json` | not possible |
| **csvpaths** | no default | no default | contents of `manifest.json`/`definition.json` | no default (needs `:uuid(...)` + instance name/index for csvpath bytes) | requires `:uuid(...)`; returns a field, or (if only `:uuid(...)`) the version's bytes | requires `:uuid(...)` + instance name/index to get a field |
| **results** | no default | no default | contents of `manifest.json` | any standard run-result file, or a user-named parquet/jinja/text file, via e.g. `:file("orders.parquet")` | field from `manifest.json` | field from any standard JSON run-result file (`errors.json`, `meta.json`, etc.) |

#### 4.17
**Note on `:uuid(...)`**: it is not a mandatory function. If a reference's
own pointer (`:first()`, `:index(n)`, etc.) already narrows to one version,
nothing else is needed. `:uuid(...)` matters when a caller wants to resolve
one *specific*, previously-queried candidate — via `resolve_from
(list[str|UUID])` — out of several results a prior `query()` returned.

### The two-call workflow

This pseudocode illustrates the approximate workflow for a simple case:

#### 4.18
```python
ref = ReferenceParser3(string="$acme.files.*.:last()", csvpaths=paths)
finder = FilesReferenceFinder3(csvpaths=paths, ref=ref)
results = finder.query()        # cheap: list of ReferenceResult3(path, uuid)
data = finder.resolve()         # or finder.resolve_from(narrowed_selection)
```
In this case, above, the resolve returns the paths to the last instance home
within every 1-level template run.

---

## 5. Functions

Functions are the mechanism for narrowing and pointing within a reference.

#### 5.1
**Form**: `:name(arg)` or `:name()` — a colon, a name, parentheses, at most
one argument. Functions chain with no separator (`:before(:yesterday()):
index(3)`) and are implicitly ANDed together without regard for order.

#### 5.2
**Arguments** can be a quoted string, a signed int, an `@name` runtime-bound
variable, a nested function call, a bare `*`, or a `/regex/` literal.

#### 5.3
**Runtime lookup, not grammar knowledge**: the grammar has zero built-in
knowledge of what functions exist — `FNAME` is just `/[a-zA-Z_][a-zA-Z0-9_]*/`.
Every function name is resolved against a name-keyed registry
(`ReferenceFunctionFactory`) at transform/build time, not parse time. This is
the central design choice that keeps the grammar flat and the opportunity
to add a custom functions capability when needed.

#### 5.4
Reference functions are self-documenting in the same way that match
functions are. They must be able to output .md in a similar way to
`csvpath/cli/function_describer.py`

### What functions do

#### 5.5
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

#### 5.6
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

#### Existing functions

#### 5.7
There must be a field accessor function for every field available in any of
the manifest.json files. Whenever it is practical and clarity is neutral or
enhanced, the same field accessors should be applied across the manifests.

#### 5.8
For a breakdown of existing functions, see:
specs/references_v3/notes/function_coverage_matrix.md

### Functions representing files

#### 5.9
The complete class of file accessors is:
- :manifest() — any of the seven manifest.json files
- :definition() — the named-files or named-paths definition.json files
- :data() — the matched data output file data.csv
- :errors() — the errors.json file
- :printouts() — the standard printouts under print-mode's combined output default
- :vars() — the vars.json file containing the end-state runtime variables
- :meta() — the meta.json file containing both the metadata key-value pairs from leading comment and the runtime indicators
- :unmatched() — the optional standard unmatched lines output to unmatched.csv
- :file("...") — arbitrary files, primarily Parquet output and print report files when print-mode is set to create separate files
- :log() — the project csvpath.log file

#### 5.10
#### The root `:manifest()` and `:definition()` file accessors
All named-things areas have global ledger `manifest.json` files tracking all
add actions (registers, loads, runs). Each named-file, named-paths group, and
named-results run has its own manifest.json, as does each instance in a name-
result.

#### 5.11
Named-files and named-paths groups may also have a definition.json file that
holds additional config information controlling how files are registered and
how named-paths groups are run. `definition.json` is common but not mandatory.

#### 5.12
Both files may be accessed by references that address all named-things and
use `:manifest()` or `:definition()` without other path info. For e.g.
`$*.files.:manifest():last()` returns the last file registration data
captured in the global files ledger manifest. To get a reference to the
manifest as a whole, simply use `:manifest()` alone.

#### 5.13
Definition file references always act on the complete JSON structure, but
can return a single field, if a field accessor is used, or return None if
a field accessor is given an appropriate match value argument. For e.g.
`$acme.files.:description(:on_arrival(:not_none()))`

#### 5.14
The only times there may not be manifests where expected are:
- There has been no registration, loading, or running activity in the project
- The missing manifest is expected in a named-thing area that has not had
  activity, even if other named-thing areas have
- Manifests have been truncated for operational reasons without CsvPath
  Framework managing that process

#### 5.15
A manifest is:
- Files ledger: list of one dict per registration
- Named-file: list of one dict per registration
- Csvpaths ledger: list of one dict per named-paths group load
- Named-paths group: list of one dict per load, each dict including a list of csvpath instances and a verbatim list of csvpath statements
- Results ledger: list of one dict per csvpath instance run
- Named-results: no master manifest is created at this level at this time
- Named-results run: dict of run values for the whole run
- Named-results run's instance: dict of run values for the csvpath statement instance

#### 5.16
The `:manifest()` function's behavior is context-aware. It says: "get
whatever manifest data is currently in scope". It resolves three ways:
- The bare files datatype ledger manifest returned by the file accessor:
  `$*.files.:manifest()`
- The acme named-file manifest returned from the file accessor
  `$acme.files.:manifest()`
- The manifest entry of the first orders.csv registration returned by the file accessor after matching within the contained list
  `$acme.files.:name("orders.csv").:first():manifest()`

### Ordinal functions

#### 5.17
- :before(int|str|datetime)
- :after(int|str|datetime)
- :from(int|str)
- :to(int|str)
- :index(int)
- :last()
- :first()

#### Ordinals and mixing ordinals

#### 5.18
References live in an ordered universe that may be stepped through using
indexes. :index() is the exemplar ordinal that picks a position. We use
the word index because the positions are countable and can be seen as a
number line. The number line is ordered by time.

#### 5.19
With one exception, the "number line" of indexed positions is specifically
instantaneous moments in an abstraction over dates. A date is an arrival
or a start time or an end time or a create time. Examples:
- Arrival — moment of registration, moment of named-paths group load
- Start — moment run starts
- End — moment run ends
- Create — moment an error is raised

#### 5.20
The one exception is the index over csvpath statements in a named-paths
group. Statements within `group.csvpaths` are ordered only by position,
meaning there is no time element to `name_three` in the `csvpaths` datatype.

#### Ordinal roles

#### 5.21
Ordinals have roles:
- Anchor — the fixed start or end of the number line for the purposes of
  other ordinals starting from the 0th index
- Direction — which way do we count to progress from index to index
- Stepping — what index position are we in the list of positions

#### Assignments of roles
#### 5.22
- :date(), :yesterday(), etc. are point-in-time anchors defining
  point-in-sequence — anchors dominate. I.e. they are the most fundamental
  positions. Unless otherwise determined, anchors are 1) arrival time, or
  2) runtime, with 1 and 2 in general not competing in the way that
  registration time does not compete with run time but does have a known
  obvious relationship based on precedence / dependency.  The number line is
  date ordered/date determined, but for the purpose of ordinals that are not
  anchors, indexed.
#### 5.23
- :before(), :after(), :from(), :to() are directions — directions are
  intermediate. I.e. a direction modifies an anchor or position
#### 5.24
- :index() is a position of a counter within a bounded number line — within
  a range defined by:
  - date anchor
  - an ordered-list position of relative to next and last indexes
  - the 0th or last position.

#### Directions, counting and mixing

#### 5.25
An index counts from the anchor. :index() counts upward by default, meaning
in an increasing direction. :index() steps down to find the starting point if
negative, but still counts upwards. I.e. `:from(5):to(-1)` counts from the 6th
position to the N - 1 position, where N is the (0-based) length - 1 of the list.

#### 5.26
If a pair of direction functions have indexes forcing up to down the index is
in principle forced to count backwards. I.e. `:from(5):to(3)` counts 5, 4, 3.
It is unclear if this will be useful or allowed in practice but it must be
grammatically possible. In the first release an exception can be raised
because we have no demand for that functionality. Care should be taken to not
preclude that possibility ever being added or make the additive capability
more difficult.

#### 5.27
Ordinals may be mixed. The mixing must make logical sense. If mixing does not
make logical sense, an error can be raised and the reference terminated. The
main heuristic is precedence and applicability. Runs depend on registrations
so registrations have a precedence advantage over runs and runs have a
dependency relationship to registrations

#### 5.28
Note: historically we have had from/to as inclusive and before/after as
exclusive. We also used from/to only with the `csvpaths` datatype. It may be
practical to only offer one of these pairs or use aliases. TBD.

### Pure value functions

#### 5.29
The complete set of dumb value-producing functions is:
- :year() — int
- :month() — int
- :month_name() — str
- :day() — int
- :day_name() — str
- :hour() — int
- :hour_24() — int
- :minute() — int
- :second() — int
- :yesterday() — datetime or str
- :today() — datetime or str
- :date("...")  — str

Note: this list may expand modestly before feature complete.

### Predicate support functions

#### 5.30
Every field accessor has the ability to match on a provided value, and thereby
filter the reference. For e.g. `$*.files.:home():definition(:on_arrival(:not_none()))`
limits the registration file homes returned to 0-level template registrations where the
named-file's `definition.json` has an `on_arrival` activation declared.

#### 5.31
The predicate support functions are those that make it possible to use predicate
matching with variable or category values.

- :true() — matches the JSON true / Python True
- :false() — matches the JSON false / Python False
- :none() — matches the JSON null / Python None
- :not_none() — value is not null / None
- :empty() — value is ""
- :not_empty() — value is not ""
- :regex(/.../) — value matches regex
- :having("...") — structure has a named/IDed child. Primary case: named-paths groups versions having a csvpath statement ID.

### Function arguments
#### 5.32
Functions may have zero or one argument. Arguments do one of three things:
- Point
- Narrow
- Match

#### 5.33
An argument that enables a function to point provides additional variable
information. For e.g. `:index(5)` is always a pointer but it only works when
it is given the information indicating which index it refers to, in this case
the 0-based `5`, meaning the 6th item.

#### 5.34
An argument that narrows enables a context-setting function to know what its
context creating constraint is. E.g. `:having("orders")` is a context setter that
needs the ID of a csvpath statement to enforce its limitation on the results of
`name_one`.

#### 5.35
An argument that matches allows a field accessor function to indicate a
limitation on its `name_one` or `name_three` results by requiring the value of
its field to match the argument it receives. Take, for e.g.,
`:errors():error_count(:above(2))`. By itself, `:error_count()` provides
access to a csvpath statement's run instance's manifest field tracking the
number of errors. But `:errors():error_count(:above(2))` is selecting the
path to a run instance's `errors.json` (on query()) and the contents of the
same `errors.json` (on resolve()) but only if there were more than `2` errors
in the run of that csvpath instance.

#### 5.36
By contrast to the last example,
`$acme.results.:last().orders:errors(:idchain("add[0]"))` returns the path
to the errors.json of the orders csvpath statement in the last acme run on
query and on resolve returns every error in the list where the first add
function generated an error resulting in an idchain of "add[0]", if any.


### `{...}` string interpolation

#### 5.37
Since a function takes at most one argument, there is no way to write a
`:concat()`. Interpolation is the mechanism instead —
`:name("partner-{@company}-orders")`,
`:name("partner-{:year()}-orders")`, `:name("partner-{:year()}-{@company}")`.
Only a bare `@variable` or a call to a `VALUE`-role function is legal
inside `{...}` — a context-setter or pointer (e.g. `:first()`, `:all()`)
is rejected, since neither produces a plain value. `{{`/`}}` escapes a
literal brace, matching the convention already used by
`csvpath/util/var_utility.py`'s `substitute()`.

#### 5.38
**Deliberately split into two phases**: actually resolving an
interpolated string into its final text needs a runtime `CsvPaths` context
(to look up `@variable` values) and at least one real `VALUE`-role function
(e.g. a future `:year()`) — neither exists yet, so this phase only builds
and validates the *shape*.

### Context-setter vs. pointer functions

#### 5.39
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
#### 5.40
- A pointer that uniquely identifies an item (file or directory) when used
  with an argument may also be used without an argument to retrieve the same
  value as a field accessor. E.g. $acme.files.:first():uuid() returns a UUID
  value; whereas, $acme.files.:uuid("ab37-fef3...") returns a path to the item
  without resolving to a more specific value. Likewise :fingerprint().
#### 5.41
- In name_one, a pointer resolves to a physical file, a named-paths group
  version, or a run.
#### 5.42
- In name_three, a pointer resolves to a well-known metadata *file* (e.g.
  `:errors()`) — unless that pointer's own argument is itself another
  pointer, in which case it resolves to a specific *value* inside that file
  instead (e.g. `:errors(:idchain())`). Same trait, one nesting level
  deeper, not a separate category.

#### 5.43
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
#### 5.4
A chain may contain any number of context setters but at most one pointer.
Critically, **a pointer used as another function's argument does not count
toward, or act as, the pointer of the chain it is nested in** — it resolves
that inner function's own internal scope. So `:errors(:idchain("..."))` is
legal (one pointer — `idchain` — at the argument level, one pointer —
`errors` — at the chain's own top level). Conversely, `:last():index(3)`
sitting side by side in the same chain is illegal (two pointers, same
level).

---

## 6. Grammar (`csvpath/references/reference_grammar_3.py`)
#### 6.1
An LALR Lark grammar is required. LALR is required to support
`parse_interactive()`-based type-ahead.

Function names, the requirement for `name_three`, or not, and other factors are
grammatically neutral and enforced during parse tree interpretation.


#### 6.2
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
by finders and for direct access to the name parts of a reference string. v3's
ReferenceParser is analogous to v1/v2's and shares parts of its interface;
however, full v3 and v2 compatibility is not a hard requirement at this time.

### Functions: `Function3` and `ReferenceFunctionFactory`

#### 6.3
- **`Function3`** (`csvpath/references/functions/function_3.py`) the base class
for real, behavior-having functions. (Note: `FunctionCall3` is the parse tree
object.)

- **`ReferenceFunctionFactory`** (`reference_function_factory_3.py`) is the
name-keyed registry for all functions. `add_function(cls)` allows for future
custom function registration.

### `ReferenceFinder3` ABC and results containers
#### 6.4
- **`ReferenceFinder3`** is an ABC taking `(*, csvpaths, ref: ReferenceParser3)`.
Using a reference has two stages:
- query
- resolve

The query stage is performed with the `query()` method. The result is a list
of path+uuid pairs, with two other fields for specific cases, as described
elsewhere.

The following resolve stage is performed with `resolve()`, and implies `query()`.
Resolve gives whole files or field values, in addition to path+uuid.

#### 6.5
Items from the list produced by `query()` may be resolved without resolving the
whole list originally returned.

#### 6.6
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

#### 6.7
`__eq__` compares all four fields (`path`+`uuid`+`data`+`identity`) — this is
what `ReferenceResults3.deduplicated()` uses to collapse true duplicates.
Different results may be returned after `resolve()` than would after only
`query()`.


### The finders
#### 6.8
`FilesReferenceFinder3`, `CsvpathsReferenceFinder3`, `ResultsReferenceFinder3`
find results based on a ReferenceParser which represents a reference string.

**What a reference results object `path` actually holds**

#### 6.9
| Producer | What `path` holds |
|---|---|
| FILES, a version match | the specific version file |
| FILES, name_one-terminal (no version pointer) | the named-file's file-home *directory* |
| CSVPATHS, any version match | the group's `group.csvpath` *file* — always the same path; only `uuid`/`identity` distinguish versions/statements |
| RESULTS, a run-level match | the run's own home *directory* |
| RESULTS, an instance-level match | the instance's own home *directory* (a subdirectory of the run) |
| Rule 1a (bare `'*'`+`:manifest()`, a global ledger — see below) | the ledger file itself, e.g. `.../manifest.json` — `uuid` always `None` |
| Rule 1b (an ordinal pointer riding with the bare global-ledger `:manifest()` — see below) | the *same* ledger file path as Rule 1a, but with a real `uuid` attached to select an entry) |



---

## Appendix: UNKNOWN CORRECTNESS / USEFULNESS

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

### Additional rule notes

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









