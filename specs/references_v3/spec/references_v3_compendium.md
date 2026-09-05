# CsvPath References v3 — Compendium

This document defines the References v3 subsystem. It incorporates the
following docs by reference:
#### Specs
- specs/references_v3/spec/requirements_for_functions.md
- specs/references_v3/spec/references_expressions.md
#### Normative examples
- specs/references_v3/spec/normative_reference_examples.txt
- specs/references_v3/spec/normative_reference_expressions_examples.txt
#### Required grammar
- csvpath/references/reference_grammar_3.py

No one doc controls. If there is a discrepency, lack of clarity, or
logical question mark, the resolution is to raise the issue to David's
attention for triage and a spec update.

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

## Outline
1. What are References v3?
2. Overall Usage Pattern
3. The Reference Model
   - root_major
   - name_one
   - name_two
   - name_three
4. Query vs. Resolve
5. Functions
6. Grammar and Implementation

---

## 1. What are References v3?

CsvPath Framework includes a CsvPath Reference Language that provides flexible
general access to the Framework's physical data and metadata model. This
language enables users to ask questions in a declarative syntax rather than
requiring them to programmatically work within the Framework's objects interface.

References are:
- Easier to use than remembering how to use numerous classes and tools
- More flexible and concise for questions practical questions
- More resiliant and safer in the face of user error
- Less brittle than adding dozens of new methods supporting new querying and reasoning tools
- More understandable when logged by an AI as it iterates through its work

References give access to CsvPath Framework data stores. There are three data
stores each holding a kind of named thing:
- **named-files** — versioned sets of registered data files, with each version
  having a cryptographic identity
- **named-paths groups** — versioned sets of CsvPath statements that are used
  as a single entity
- **named-results** — sets of run outputs from applying a named-paths group
  to a named-file

CsvPath has two prior versions of CsvPath Reference Language:

- **v1** set the basic syntax users see everywhere (e.g. `$myfile.files.abc`)
- **v2** updated the parsing/resolving implementation behind that same syntax

**v3 is a from-scratch replacement**, motivated by two things:
- v1 and v2 have real tech debt and lack conceptual clarity
- The vision of a more robust reference language giving an AI assistant
a single, concise, general-purpose exploration tool for digging into CsvPath
Framework project states, instead of requiring many narrow, brittle,
purpose-built tools.

The most obvious differences between v2 and v3 are are covered below:
- v3's heavy use of functions
- The option to use variables
- The option to perform set operations using reference expressions

v3 is AI-facing only, for now. v1/v2 stay exactly where they are, untouched,
and remain what end users see (identifying runs, registrations, named-paths
loads). v3 lives in a new location, `csvpath/references/`, and follows v1/v2's
naming convention: `_3.py` files, `3`-suffixed class names (`ReferenceParser3`).
v3 tests live in `tests/references/`.

v3 covers only named-file, named-paths-group, and named-results storage. I.e
the `files`, `csvpaths`, and `results` datatypes introduced below. It does not
cover the four runtime datatypes (variables, headers, csvpath match state,
metadata) used as primary CsvPath Validation Language productions and in
`print()` and `error()` statements. Those will be addressed in a follow-on
release post v3's launch.

---

## 2. Overall Usage Pattern

A reference is a string that is interpreted as a query giving access to
four types of data:
- File paths
- Identifiers (UUIDs and fingerprints)
- Other individual metadata field values
- Full data and metadata file contents

References can query and resolve. Querying finds the location and identity
of entities. Resolving retrieves field values, the full contents of files,
and the full value of file-like entities (e.g. a named-paths group).

A reference can only resolve the full contents of a single file or file-like
entity. A query can return multiple files, but attempting to resolve (i.e.
read) multiple files at once raises an error.

#### 2.1
The steps to using a reference are:
1. Parse a reference string into a reference object
2. Create a finder that will interpret the reference
3. Register any required variables with the finder
4. Use the finder's `query()` to get a list of paths+UUIDs
5. If needed, use `resolve()` to get file contents or a metadata field

#### 2.2
References may be used within a lightweight expression language (also
considered part of CsvPath Reference Language) that enables the user to
structure set operations on references. These reference expressions set
operations are:
- UNION
- INTERSECT
- SUBTRACT

#### 2.3
Most reference expressions requirements are in
`specs/references_v3/spec/references_v3_expressions.md`

---

## 3. The Reference Model

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
| `name_one` | yes | An entity. |
| `name_two` | optional, files only | An XLSX worksheet identifier, written as `#worksheet_name` appended directly to name_one's path. |
| `name_three` | optional | A more specific part of the entity name_one identified. |

The names `root_major`/`name_one`/`name_two`/`name_three` are inherited from
v1/v2's naming and are kept for continuity and because they make sense in
context even if they aren't obvious names. v1/v2 also allows for a
`name_four` based on a separator, `#`, same as is used to create name_two.
`name_four` has few use cases, is rarely used, and is only applicable to the
runtime datatype `variables`. It does not make an appearance in v3.

### The role of functions

#### 3.4
Note: high level requirements for functions began in
`specs/references_v3/spec/requirements_for_functions.md` and continue in this
spec.

#### 3.5
Functions look like `:name_of_function()` and can take 0 or 1 argument, which
is a:
- String
- Number
- Function
- Regex string wrapped in forward slashes (`/.../`)
- Variable

There is more information on functions below in their own section.

### The role of variables

#### 3.6
Variables can be set on the finder and used within references. They must be
set prior to calling either the query or resolve method. A variable can be
any Python object, but the variable value will be put into a string context so
its __str__() must make sense to the reference.

Variable syntax is `@` name, as in `@myvariable`.

Setting variables is done on the finder using these methods:
#### 3.7
```
    def variables(self) -> dict:
        ...
    def set_variable(self, name: str, *, value) -> None:
        ...
    def set_variables(self, variables: dict) -> None:
        ...
```

---

### `root_major`

#### 3.8
`root_major` is the name of a named-file, named-paths group, or named-results
entity, depending on if the datatype of the reference is `files`, `csvpaths`,
or `results`, respectively. `root_major` can take:
- A string
- A `*`
- A variable in the form `@varname`
- A `:regex(...)` function

`*` means any existent named entity

---

### `name_one`
#### 3.9
`name_one` means structurally different things per datatype. It points to:
- `files`: a file home
- `csvpaths`: a version of a named-paths group's `group.csvpath` file
- `results`: a run dir

`name_one` for files and results is a file system namespace closely related
to the physical file system layout.

A **file home** is a directory named by the original file name containing
registered versions of that file

A **run dir** is a directory named by a disambiguated second-resolution
datetime (e.g. `2026-01-01_01-01-01`) containing run metadata and the
directories containing the output of each csvpath in the named-paths group

#### 3.9a
`name_one` cannot be `""` and a reference must have a `name_one`. A reference
cannot end on a `.`.

#### 3.9b
The `name_one` position cannot start with a `/`. Paths are relative to the
named-file home. As well, `name_one` cannot end in a `/`. Any legal syntax
fills this requirement. For e.g. the first two of the following three
references is legal, the third is not:
- `$acme.files.orders/*`
- `$acme.files.orders/:manifest()`
- `$acme.files.orders/`

#### 3.9c
`name_one` supports functions, described below. It also supports a `*`
wildcard that matches any name segment of a path (`files`, `results`) or
any version (`csvpaths`). Wild cards are discussed below. A function
starting `name_one` or following directly after a path separator implies
a `*` wildcard, unless it falls in one of these categories of exceptions:

- It is itself a wildcard: `:all()`, `:flatten()`, `:groups()`
- It fully occupies a path segment. E.g. `:name()`, `:regex()`, `:choice()`
- It doesn't operate as or in a path segment at all. E.g. `:manifest()`,
`:definition()`, `:on_arrival()`, `:fingerprint()`, etc.

More specifically:
- `:all()` is a form of wildcard itself, so there is no implication of `*`
- `:flatten()` is the n-level form of `*`, so it supersedes `*`
- `:groups()` is the n-level form of `:all()`; again not implying `*`
- `:name(...)` and its equivalents fully occupy the path segment they
occupy, precluding the possibility of a wildcard at that location
- A `:manifest()` standing alone in `name_one` with entity name `*`
always points to the datatype's ledger manifest, not those of individual
named-entities or the events that happen within them.
- A `:manifest()` standing alone in `name_one` with a specific entity name
implies a `*` in the case of the `results` datatype, there being one
manifest file per run; however, in the case of `files`, and `csvpaths` the
reference is to the entity's manifest file and no `*` is implied.
- `:definition()` in a named-file or named-paths group `name_one` always
refers to the named-entity's sole definition file, which has no
relationship to template path; therefore, a `*` is not implied.
- Functions that directly address definition fields, e.g. `:on_arrival()`,
likewise, do not imply `*`.

Note that `:regex(...)` and `:choice(...)` are pattern-matching analogs
of `:name(...)`.

#### 3.9d
The following two `name_one` values are functionally the same:
- `$acme.files.:type("csv")`
- `$acme.files.*:type("csv")`

Likewise the following two references:
- `$acme.files.orders/:type("csv")`
- `$acme.files.orders/*:type("csv")`


### `name_one` and Time
#### 3.10
Datetime functions exist, as discussed below, that can be used wherever a
time dimension is available. In `name_one` the time dimension exists for
`csvpaths` and `results`.

Named-paths group loads are time-bound. The load time is carried in
`name_one`; therefore, datetime functions are available in `name_one`.

Likewise for `results`, there is a time dimension to `name_one`. `name_one`
represents a run which begins at a moment in time. The run's start time, at the
granularity of a second, becomes the run dir name. This means that the path
namespacing includes a datetime-derived path segment. Separate from the path,
datetime information is also carried in `name_one`, allowing the use of datetime
functions.

There is no time dimension in `name_one` for `files`. File registrations
are time-bound; however, the datetime information is carried with the version
registered, in `name_three`, not with the namespaced location of the file home.

#### 3.11 Example finding a file registration by arrival time
Given a named-file `acme`, to find the first registration in any location
within `acme` that happened yesterday we do:
```
$acme.files.*.:yesterday():first()
```
Where `*` is `name_one` and the datetime information is carried in
`name_three`.

### `name_one` and Templates
#### 3.11
Templates are used to set the location of a registered file within a
named-file or run dir within named-results. `csvpaths` does not use templates

Templates are merged at registration or run time with:
- The path to the original location of a registered file
- Datetime tokens (e.g. `:day`, `:year`) representing the current moment
A named-file template must end in `:filename`, indicating the file home. A
named-results template must end in `:run_dir`, indicating the run dir
(a.k.a. run home).

`files` and `results` datatype entities are found at 0 or more path segments
below the named-file or named-result home dir. The specific location is set by
passing a template during registration or when a run is started. References
include path segments, if any, in `name_one`.

We speak of 0-level, 1-level, 2-level templates, etc. to describe how many
path segments the template adds to the path to the home directory.

#### 3.12 Examples
Given a file at `acme/orders/2026/march/q1.csv` registered into `acme`.
- A template `` registers the file home `named_files/acme/q1.csv`
- A template `EMEA/:filename` registers the file home `named_files/acme/EMEA/q1.csv`
- A template `:1/:year/:filename` registers the file home `named_files/acme/orders/2026/q1.csv`

The first is a 0-level template (a.k.a. no template, implying `:filename`).
The second is a 1-level template. The third is a 2-level template. Examples
for `results` would be essentially the same.

Regardless of the number of levels, the `:filename` or `:run_dir` must be
represented in the reference. The representation is one of:
- A string
- A function
- The `*`
- A variable

A string could look like `2026-01-01_01-01-01` or `orders.csv`.

Typical `name_one` functions include:
- `:all()`
- `:name(...)`
- `:flatten()`
- `:group()`
- `:regex("2026-01")`

#### 3.13
A 0-level template (a.k.a. no template) is effectively just the home token.
I.e. `:run_dir` or `:filename`. 0-level template named-file registrations have
their file homes directly below the named-file home. Likewise a run started
with 0-level template (i.e., in practice, no template) has its run dir (a.k.a.
run home) directly below the named-results home directory.

#### 3.14 Examples
Given a template `:0/:filename` and a file at `orders/2026/march.csv` a
registration under the `acme` named file would result in this path:
`named_files/acme/orders/march.csv` and could be found with the following
references.
- Exact path match returning path+uuid to file home
`$acme.files.orders/:name("march.csv")`
- The last of the 1-level registrations
`$acme.files.*/*.:last()
- The last of all registrations without regard for template levels
`$acme.files.:flatten().:last()
- The path+uuid of all versions of 1-level template file homes starting with "march"
`$acme.files.*/:regex("^march")

### `name_one` For the `csvpaths` Datatype
#### 3.15
**`csvpaths`**: name_one is a version-selecting expression, not a path. A
named-paths group has exactly one `group.csvpath` file on disk, updated in
place every time statements are (re)loaded. There is no per-version physical
file. Versioning instead lives entirely in the group's `manifest.json`.

#### 3.16
Despite a verion's source being the manifest, each version of a named-paths
group is equivalent to a file, and therefore only one version can be retrieved
in full in one reference. This limitation is applied to other file and file-like
records, for example, the standard `errors.json` file found in `results`.

The manifest is an array of load events, each containing
the complete text of the group's csvpath statements at that load. So for
`csvpaths`, `name_one` selects one or more entries in that manifest array
by:
- Load datetime
- Load index
- Another ordinal function
- The UUID assigned at a load event

#### 3.17
Every result shares the same `group.csvpath` path, differentiated only by
the named-paths group version's UUID (i.e. the manifest entry's identifying UUID).

#### 3.18 Examples
Given a named-paths group `acme` loaded three times one day apart, at:
- 2026-11-05 with UUID `2fc1995b2...`
- 2026-11-06 with UUID `a8ab152c2...`
- 2026-11-07 with UUID `091cb1fed...`

Expect the following references to have these results:
- `$acme.csvpaths.:last()` retrieves the 3rd version loaded on 2026-11-07 as `named_paths/acme/group.csvpaths` + UUID `091cb1fed...`
- `$acme.csvpaths.*` retrieves all versions as:
  - `named_paths/acme/group.csvpaths` + UUID `2fc1995b2...`
  - `named_paths/acme/group.csvpaths` + UUID `a8ab152c2...`
  - `named_paths/acme/group.csvpaths` + UUID `091cb1fed...`
- `$acme.csvpaths.:date("2026-11-05"):after():first()` retrieves the 2nd version as `named_paths/acme/group.csvpaths` + UUID `a8ab152c2...`

Note that the finder's `query()` method with reference `$acme.csvpaths.*` returns the three results shown above; however, the `resolve()` method raises an error because it is not possible to load multiple full documents at once and each version of a named-paths group is considered the equivalent of a document, even though it is sourced from a versioning key in the manifest entries.

---

### `name_three`
#### 3.19
`name_three` points to one or more entity parts of the entity or entities indicated
by `name_one`. The `name_three` entities are:
  - For `files`: a specific cryptographically identified version of a named-file
  - For `csvpaths`: a csvpath statement contained in a named-paths group
  - For `results`: the specific results of running a csvpath statement contained in
    the named-paths group used in the run

`name_three` can be:
- A string
- A variable
- A function
- The `*`

When `name_three` is a string or variable, the name is that of the entity:
- For `files`: the fingerprint of the bytes registered as a version of the named-file
- For `csvpaths`: the identity (ID or name metadata key) of a csvpath in the group
- For `results`: the identity (ID or name metadata key) of a csvpath in the named-paths group

#### 3.20 Examples

- `$acme.files.:name("orders.csv").:last()` returns the last version under the given
file home within `acme`.

- `$acme.csvpaths.:last().:after("header_checks")` returns the sequence of csvpaths statements starting from the one following the statement with the identity `header_checks` from the last version of the `acme` named-paths group.

- `$acme.results.:groups()/:from(:index(-2)):to(:index(-1)).header_checks:error_count()` returns the last two error counts of the runs that had a `header_checks` csvpath instance for all runs by template.



### Structure Breakdown Table

#### 3.21
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



---

## 4. Wildcards: `:all()` vs. `*`

There are four wildcards:

| flat     | grouping |
|----------|----------|
| `*`      | `:all()` |
| `:flatten()` | `:groups()` |

`*` flattens every wildcard position in the reference into one pooled
search space.

`:all()` anywhere in the `name_one` groups the remaining `name_one` search space by the
names found at the grouping segment (`:all()`'s position). The reference processes each
group independently of the other groups. That means that a `:last()` function that follows an
`:all()` will give the last item found by looking solely at its group scope. At the same time
the reference as a whole gains the possibility of having one last item per name found in the
position occupied by the `:all()`.

Note these limitations on grouping:
- `name_one` can have only one `:all()` or `:groups()`
- `:all()` cannot be combined with `:groups()`
- `name_three` can have only one `:all()`
- `name_three` does not accept `:groups()`
- in `name_three`, `:all()` only has grouping power in `results` where there is further search space to group


#### Example 4.1
Given named-file `alpha` with paths:
- `zero.csv` [1 version]
- `one.csv` [2 versions]

And named-file `beta`:
- `two.csv` [2 versions]

And named-file `cappa`:
- `three.csv` [1 version]
- `orders/2026/four.csv` [2 versions

Expect the following results from these references:
- `$*.files.*.:last()` → 1 most-recent registration, considering all named-files
- `$*.files.:all().:last()` → 4 most-recent registrations, one per 0-length template file home
- `$alpha.files.*.:last()` → 1 most-recent registration from `alpha`
- `$alpha.files.:all().:last()` → 2 most-recent registrations, one per file home
- `$*.files.:groups().:last()` → 5 most-recent registrations, one per file home
- `$*.files.:flatten().:from(4):to(:index(-1))` → last 4 most-recent registrations of all 8

Note that the following references are equivalent. While References v3 prefers to have 1 way to do things, not multiple ways, these examples fall naturally out of desirable behavior, so are acceptable redundancies.
- `$*.files.:flatten().:all()` → all 8 most-recent registrations
- `$*.files.:flatten().*` → all 8 most-recent registrations
- `$*.files.:groups().*` → all 8 most-recent registrations
- `$*.files.:groups().:all()` → all 8 most-recent registrations


---


## 5. Query vs. Resolve

References v3, like v2, splits reference-following into two phases, but the phases mean
something different in v3.

#### 5.1
**Query**: runs the reference as a search and returns 0-or-more results. Each
is the set of:
1. A file-system path
2. A UUID
3. Optionally a name identifing a sub-unit, either:
   - The `name_two` field (Excel files only)
   - An instance ID (`csvpaths` only)

#### 5.2
These results always point to a file system location, with the identifiers
needed for any internal file pointer (for Excel files and `group.csvpaths`).
This even when the reference is clearly pointing to a metadata field
within that context. In the query stage, a user can trim the list of results
according to path, UUID, etc. without accessing whole files. In some cases
a reference expression may combine two references, when both sets of results
are comparable without further resolution.

#### 5.3
The `query()` method always succeeds (presuming a properly written reference).
Queries may refer to multiple files. The contents of a file can be retrieved
using `resolve()`. However, if multiple results of a `query()` would retrieve
file contents, an error is raised by `resolve()`.

The rule is:
- `query()` can return multiple file paths
- `resolve()` can only retrieve one file's content and errors if there are
  multiple file paths for the reference

#### 5.4
Tangental to the rule of 4.2, a wildcard `root_major` in any datatype where
name_one is `:manifest()` points to the ledger manifest for that datatype.

#### 5.5
E.g. `$*.files.:manifest()` is a pointer to the path of the named-files
ledger manifest. That manifest does not have its own UUID; therefore, the
reference result object's UUID field is None. The manifest also does not
have a `name_two` or `name_three` identity, and therefore the identity field
also remains None. In that example, individual registrations, or their
fields, can be retrieved from the manifest. Likewise, the set of all
registrations within the manifest can be retrieved.

#### 5.6
Note that a run record in the `results` ledger manifest is not the same
as as a run manifest for an instance of a csvpath in a run. The former is
not a file, the latter is a file. You can pull multiple complete run records
from the `results` ledger manifest, but you cannot retrieve multiple
instance-level results manifest files at the same time.

#### 5.7
If a reference retrieves multiple records from a ledger the UUID of the
reference result object remains None. If the reference retrieves one record
the UUID of the reference result is the UUID of that ledger entry. In
either case, the reference result object's path remains that of the ledger
manifest file.

#### 5.8

Note that `:definition()` has no global ledger. A reference like
`$*.files.:definition()` will raise an error.

#### 5.9
**Resolve**: pulls actual content a reference points to. When a reference
points to a file, resolving returns either bytes (if the reference is to a
binary file, such as an `.xlsx`) or a JSON structure. When a reference
points to a field the return is a string, int, date, UUID, etc.

#### 5.10
It is possible for resolve to return no answer (`None`). A bare results
reference with no metadata pointer has no single well-defined resolve output
of a run; only the path to the run is indicated and that is available in the
query stage.

### Query, by termination point

#### 5.11
A Query terminating at name_one (regardless of any pointer function) is primarily a path,
which may be resolved to a value, if further resolution of the reference is possible.

#### 5.12
| Datatype | What name_one-terminated query() returns |
|---|---|
| files | path to the named-file's file-home directory (directory of version files) |
| csvpaths | path to the `group.csvpath` file |
| results | path to the run directory |

#### 5.13
A query terminating at name_three:

| Datatype | What name_three-terminated query() returns |
|---|---|
| files | path to the specific version file |
| csvpaths | path to the `group.csvpath` file (same path as always; the combined version UUID and statement ID differ) |
| results | path to the specific statement's instance directory within the run dir |

### Resolve — the three-way classification

#### 5.14
A reference resolves to a 0 or more set of one of three kinds of thing:

1. **First-party registered data** — the actual underlying content — returned
#### 5.15
   when no function names metadata at all (e.g. a plain files reference with a
   version pointer resolves to that version file's raw bytes).
2. **File contents**
#### 5.16
   - A whole results metadata or result data file — returned when a function names
   a known metadata file (`:errors()`, `:vars()`, `:meta()`, or an arbitrarily-
   named file via `:file(...)`) with no further drilling into it.
#### 5.17
   - A manifest.json or definition.json file — file contents of one of the two
   main config files. Note all datatypes have `manifest.json` but only `files`
   and `csvpath` have `definition.json`.
3. **One metadata field** — based on combining a file accessor and a field accessor.
#### 5.18

Note the ways file accessors relate to field accessors. Given a reference
that finds the last `results` run and using the `:idchain()` field accessor:

#### 5.19
`$acme.results.:last().:errors()` — returns the path+uuid, and resolves to content of file
`$acme.results.:last().:errors(:idchain(:not_none()))` — returns the path+uuid, and resolves to all errors that have idchains
`$acme.results.:last().:errors(:idchain("add[0]"))` — returns the path+uuid, and resolves to all errors with matching idchains
`$acme.results.:last().:errors():idchain(:not_none())` — returns path+uuid, and resolves to contents, iff idchain exists in file
`$acme.results.:last().:errors():idchain("add[0]")` — returns path+uuid, and resolves to contents, iff idchain matching exists in file

#### 5.20
`:idchain()` and similar functions must be smart enough to look into a JSON
structure in the right place to find the value they operate on. In the case
of idchains, the function must know to look at the `idchain` key of each
error dictionary in the list contained by `errors.json`.

The full resolve matrix by termination point and pointer kind:
#### 5.21
| | name_one, no pointer | name_three, no pointer | name_one, file pointer | name_three, file pointer | name_one, field pointer | name_three, field pointer |
|---|---|---|---|---|---|---|
| **files** | no default → `None` | version file bytes (name_three always points) | contents of `manifest.json`/`definition.json` | version file bytes | field from `manifest.json`/`definition.json` | not possible |
| **csvpaths** | no default | no default | contents of `manifest.json`/`definition.json` | no default (needs `:uuid(...)` + instance name/index for csvpath bytes) | requires `:uuid(...)`; returns a field, or (if only `:uuid(...)`) the version's bytes | requires `:uuid(...)` + instance name/index to get a field |
| **results** | no default | no default | contents of `manifest.json` | any standard run-result file, or a user-named parquet/jinja/text file, via e.g. `:file("orders.parquet")` | field from `manifest.json` | field from any standard JSON run-result file (`errors.json`, `meta.json`, etc.) |

#### 5.22
**Note on `:uuid(...)`**: it is not a mandatory function. If a reference's
own pointer (`:first()`, `:index(n)`, etc.) already narrows to one version,
nothing else is needed. `:uuid(...)` matters when a caller wants to resolve
one *specific*, previously-queried candidate — via `resolve_from
(list[str|UUID])` — out of several results a prior `query()` returned.

### The two-call workflow

This pseudocode illustrates the approximate workflow for a simple case:

#### 5.23
```python
ref = ReferenceParser3(string="$acme.files.*.:last()", csvpaths=paths)
finder = FilesReferenceFinder3(csvpaths=paths, ref=ref)
results = finder.query()        # cheap: list of ReferenceResult3(path, uuid)
data = finder.resolve()         # or finder.resolve_from(narrowed_selection)
```
In this case, above, the query returns the paths to the last version
within every 1-level template file registration under the `acme` named-file.
Note that if there is more than one such path, attempting `resolve()` will
raise an error because only one file contents can be retrieved per reference.

---


## 6. Functions

Functions are the mechanism for narrowing and pointing within a reference.

#### 6.1
**Form**: `:name(arg)` or `:name()` — a colon, a name, parentheses, at most
one argument. Functions chain with no separator (`:before(:yesterday()):
index(3)`) and are implicitly ANDed together without regard for order.

#### 6.2
**Arguments** can be a quoted string, a signed int, an `@name` runtime-bound
variable, a nested function call, a bare `*`, or a `/regex/` literal.

#### 6.3
**Runtime lookup, not grammar knowledge**: the grammar has zero built-in
knowledge of what functions exist — `FNAME` is just `/[a-zA-Z_][a-zA-Z0-9_]*/`.
Every function name is resolved against a name-keyed registry
(`ReferenceFunctionFactory`) at transform/build time, not parse time. This is
the central design choice that keeps the grammar flat and the opportunity
to add a custom functions capability when needed.

#### 6.4
Reference functions are self-documenting in the same way that match
functions are. They must be able to output .md in a similar way to
`csvpath/cli/function_describer.py`

### What functions do

#### 6.5
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

#### 6.6
Note that in reference expressions, as defined elsewhere, values may be
compared by function type and retrieved value. `:fingerprint()` retrieves
a string. A reference expression would not accept a comparison of
`:fingerprint()` to `:type()` because the function types do not serve the
same conceptual purpose, making the values not the same, regardless of
actual bytes value.

- A comparison of `:named_paths_name()` to `:named_results_name()` would
  work because names are conceptually the same kind of thing.
- A comparison of `:named_file_name()` to `:fingerprint()` would not work
  because names and fingerprints are not the same kind of thing.
- `:uuid()` and `:run_uuid()` are comparable.

#### 6.7
This makes it important to know the purpose of the function in order to use
it correctly for comparison. The taxonomy for existing functions is this
set of groupings:
  - "uuid": :uuid(), :run_uuid(), :named_file_uuid(), :named_paths_uuid()
  - "name": :named_paths_name(), :named_results_name(), :named_file_name()
  - "fingerprint": :fingerprint(), :named_file_fingerprint() (Note:
    `:file_fingerprints()` is list-valued so does not compare in practice)
  - "type": :type()
  - Everything else (:host(), :status(), :template(), :archive(),
    :identity(), etc.) is undeclared, for now, and falls back to
    exact-accessor-equality required for value comparison

#### Using UUID in set operations as an example of field comparisons
#### 6.8
First two simple examples:
- Get uuids from all registrations
`$*.files.:manifest():uuid()`
- Get all acme registration uuids
`$acme.files.:manifest():uuid()`

Now two example set operations that match/join on fields, UUID in this case.
- Get all registration UUIDs, except those of the acme named-files
```
$*.files.:manifest():uuid()
SUBTRACT
$acme.files.:manifest():uuid()
```

- Get all the most recent acme registration UUIDs that have been used in runs
```
$acme.files.:manifest():uuid()
INTERSECT
$*.results.:flatten():manifest():named_file_uuid()
```

#### 6.9
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

#### 6.10
There must be a field accessor function for every field available in any of
the manifest.json files. Whenever it is practical and clarity is neutral or
enhanced, the same field accessors should be applied across the manifests.

#### 6.11
For a breakdown of existing functions, see:
specs/references_v3/notes/function_coverage_matrix.md

### Functions representing files

#### 6.12
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
- :log() — the project csvpath.log file, discussed below
- :readme() — the named-file or named-paths group `README.md` file.


Note that readme files are generated in the named-file home and named-paths home by default. The function assumes they exist. A reference to a non-existent readme returns None on `resolve()`. `:readme()` is only available in `name_one`, and only in `files` and `csvpaths`, because only named-paths and named-files homes have readme files that are generated by the system.

### Manifests
#### 6.13
A manifest is:
- Files ledger: list of one dict per registration
- Named-file: list of one dict per registration
- Csvpaths ledger: list of one dict per named-paths group load
- Named-paths group: list of one dict per load, each dict including a list of
  csvpath instances and a verbatim list of csvpath statements
- Results ledger: list of one dict per csvpath instance run
- Named-results: no master manifest is created at this level at this time
- Named-results run: dict of run values for the whole run
- Named-results run's instance: dict of run values for the csvpath statement
  instance

#### 6.14
The `:manifest()` function's behavior is context-aware. It says: "get
whatever manifest data is currently in scope". It resolves three ways:
- Ledger manifest
- Named-entity manifest
- Entry representing the `name_three` item in the named-entity manifest

#### 6.15 Examples
- The bare files datatype ledger manifest returned by the file accessor:
  `$*.files.:manifest()`
- The acme named-file manifest returned from the file accessor:
  `$acme.files.:manifest()`
- The manifest entry of the first orders.csv registration returned by the file
  accessor after matching within the contained list:
  `$acme.files.:name("orders.csv").:first():manifest()`

### The root `:manifest()` and `:definition()` file accessors
#### 6.16
All named-things areas have global ledger `manifest.json` files tracking all
add actions (registers, loads, runs). Each named-file, named-paths group, and
named-results run has its own manifest.json, as does each instance in a name-
result.

#### 6.17
Named-files and named-paths groups may also have a definition.json file that
holds additional config information controlling how files are registered and
how named-paths groups are run. `definition.json` is common but not mandatory.

#### 6.18
Both files may be accessed by references that address all named-things and
use `:manifest()` or `:definition()` without other path info. For e.g.
`$*.files.:manifest():last()` returns the last file registration data
captured in the global files ledger manifest. To get a reference to the
manifest as a whole, simply use `:manifest()` alone.

Ledger and entity manifest files can be implicit in a reference, made obvious
by the context. References to fields in `:definition()` must explicitly
reference the source file using the `:definition()` function.

#### 6.19 Examples

The following two references both searches the `acme` manifest for a
registration with the given fingerprint, returning the path+uuid to that
version, if found.
- `$acme.files.:fingerprint("a28b1105c...")`
- `$acme.files.:manifest():fingerprint("a28b1105c...")`

The following two references both return a list of the registration
fingerprints found in `acme`.
`$acme.files.:fingerprint()`
`$acme.files.:manifest():fingerprint()`

The following two references search the ledger manifest for the given
fingerprint across all named-files, returning the path+uuid to that version,
if found.
`$*.files.:fingerprint("a28b1105c...")`
`$*.files.:manifest():fingerprint("a28b1105c...")`

The following reference returns the arrival activation field value. Using
`:definition()` to indicate where the `:on_arrival()` field is found is not
optional because it is a `definition.json` field, not a `manifest.json`
field.
`$acme.files.:definition():on_arrival()`

The following reference returns the definition JSON structure on `resolve()`
if an arrival activation is found; otherwise, it returns None.
`$acme.files.:definition(:on_arrival(:not_none()))`

#### 6.20
The only times there may not be manifests where expected are:
- There has been no registration, loading, or running activity in the project
- The missing manifest is expected in a named-thing area that has not had
  activity, even if other named-thing areas have
- Manifests have been truncated for operational reasons without CsvPath
  Framework managing that process


#### 6.21
A `:log()` must be available `name_one` as a standalone, not-combinable
function. It provides access to the raw log file usually configured to
be at `logs/csvpath.log`.

This is an outlier function because it is not connected to just one
datatype. It exists as a convenience for users that can more easily
manipulate references than call functions. Case in point, agents that
have full range of motion to use reference expressions but may not
have a tool context where they can run python scripts that could pull
the log file. This makes it a practicality-over-logical-fit feature.

Retrieving the main log file is one of:
- `$*.files.:log()`
- `$*.results.:log()`
- `$*.csvpaths.:log()`

An optional int argument indicates how many of the most recent lines to
return. `$*.csvpaths.:log(10)` returns the last 10 lines of the log.
Without the argument all lines are returned.

### Ordinal functions
#### 6.22
- :before(int|str|datetime)
- :after(int|str|datetime)
- :from(int|str)
- :to(int|str)
- :index(int)
- :last()
- :first()

#### Ordinals and mixing ordinals
#### 6.23
References live in an ordered universe that may be stepped through using
indexes. :index() is the exemplar ordinal that picks a position. We use
the word index because the positions are countable and can be seen as a
number line. The number line is ordered by time.

#### 6.24
With one exception, the "number line" of indexed positions is specifically
instantaneous moments in an abstraction over dates. A date is an arrival
or a start time or an end time or a create time. Examples:
- Arrival — moment of registration, moment of named-paths group load
- Start — moment run starts
- End — moment run ends
- Create — moment an error is raised

#### 6.25
The one exception is the index over csvpath statements in a named-paths
group. Statements within `group.csvpaths` are ordered only by position,
meaning there is no time element to `name_three` in the `csvpaths` datatype.

#### Ordinal roles
#### 6.26
Ordinals have roles:
- Anchor — the fixed start or end of the number line for the purposes of
  other ordinals starting from the 0th index
- Direction — which way do we count to progress from index to index
- Stepping — what index position are we in the list of positions

#### Assignments of roles
#### 6.27
- :date(), :yesterday(), etc. are point-in-time anchors defining
  point-in-sequence — anchors dominate. I.e. they are the most fundamental
  positions. Unless otherwise determined, anchors are 1) arrival time, or
  2) runtime, with 1 and 2 in general not competing in the way that
  registration time does not compete with run time but does have a known
  obvious relationship based on precedence / dependency.  The number line is
  date ordered/date determined, but for the purpose of ordinals that are not
  anchors, indexed.

#### 6.28
- :before(), :after(), :from(), :to() are directions — directions are
  intermediate. I.e. a direction modifies an anchor or position

#### 6.29
- :index() is a position of a counter within a bounded number line — within
  a range defined by:
  - date anchor
  - an ordered-list position of relative to next and last indexes
  - the 0th or last position.

#### Directions, counting and mixing
#### 6.30
An index counts from the anchor. :index() counts upward by default, meaning
in an increasing direction. :index() steps down to find the starting point if
negative, but still counts upwards. I.e. `:from(5):to(-1)` counts from the 6th
position to the last position.

#### 6.31
If a pair of direction functions have indexes forcing up to down the index is
in principle forced to count backwards. I.e. `:from(5):to(3)` counts 5, 4, 3.
It is unclear if this will be useful or allowed in practice but it must be
grammatically possible. In the first release an exception can be raised
because we have no demand for that functionality. Care should be taken to not
preclude that possibility ever being added or make the additive capability
more difficult.

#### 6.32
Ordinals may be mixed. The mixing must make logical sense. If mixing does not
make logical sense, an error can be raised and the reference terminated. The
main heuristic is precedence and applicability. Runs depend on registrations
so registrations have a precedence advantage over runs and runs have a
dependency relationship to registrations

#### 6.33
Note: historically we have had from/to as inclusive and before/after as
exclusive. We also used from/to only with the `csvpaths` datatype. It may be
practical to only offer one of these pairs or use aliases. TBD.

### Pure value functions
#### 6.34
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
#### 6.35
Every field accessor has the ability to match on a provided value, and thereby
filter the reference.

For e.g. `$*.files.:definition(:on_arrival(:not_none()))`
limits the registration file homes returned to 0-level template registrations where the
named-file's `definition.json` has an `on_arrival` activation declared.

#### 6.36
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
#### 6.37
Functions may have zero or one argument. Arguments do one of three things:
- Point
- Narrow
- Match

#### 6.38
An argument that enables a function to point provides additional variable
information. For e.g. `:index(5)` is always a pointer but it only works when
it is given the information indicating which index it refers to, in this case
the 0-based `5`, meaning the 6th item.

#### 6.39
An argument that narrows enables a context-setting function to know what its
context creating constraint is. E.g. `:having("orders")` is a context setter that
needs the ID of a csvpath statement to enforce its limitation on the results of
`name_one`.

#### 6.40
An argument that matches allows a field accessor function to indicate a
limitation on its `name_one` or `name_three` results by requiring the value of
its field to match the argument it receives. Take, for e.g.,
`:errors():error_count(:above(2))`. By itself, `:error_count()` provides
access to a csvpath statement's run instance's manifest field tracking the
number of errors. But `:errors():error_count(:above(2))` is selecting the
path to a run instance's `errors.json` (on query()) and the contents of the
same `errors.json` (on resolve()) but only if there were more than `2` errors
in the run of that csvpath instance.

#### 6.41
By contrast to the last example,
`$acme.results.:last().orders:errors(:idchain("add[0]"))` returns the path
to the errors.json of the orders csvpath statement in the last acme run on
query and on resolve returns every error in the list where the first add
function generated an error resulting in an idchain of "add[0]", if any.


### `{...}` string interpolation
#### 6.42
Since a function takes at most one argument, there is no way to write a
`:concat()`. Interpolation is the mechanism instead —
`:name("partner-{@company}-orders")`,
`:name("partner-{:year()}-orders")`, `:name("partner-{:year()}-{@company}")`.
Only a bare `@variable` or a call to a `VALUE`-role function is legal
inside `{...}` — a context-setter or pointer (e.g. `:first()`, `:all()`)
is rejected, since neither produces a plain value. `{{`/`}}` escapes a
literal brace, matching the convention already used by
`csvpath/util/var_utility.py`'s `substitute()`.

### Context-setter vs. pointer functions
#### 6.43
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
#### 6.44
- A pointer that uniquely identifies an item (file or directory) when used
  with an argument may also be used without an argument to retrieve the same
  value as a field accessor. E.g. $acme.files.:first():uuid() returns a UUID
  value; whereas, $acme.files.:uuid("ab37-fef3...") returns a path to the item
  without resolving to a more specific value. Likewise :fingerprint().
#### 6.45
- In name_one, a pointer resolves to a physical file, a named-paths group
  version, or a run.
#### 6.46
- In name_three, a pointer resolves to a well-known metadata *file* (e.g.
  `:errors()`) — unless that pointer's own argument is itself another
  pointer, in which case it resolves to a specific *value* inside that file
  instead (e.g. `:errors(:idchain("add[0]"))`). Same trait, one nesting level
  deeper, not a separate category.

#### 6.47
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
#### 6.48
A chain may contain any number of context setters but at most one pointer.
Critically, **a pointer used as another function's argument does not count
toward, or act as, the pointer of the chain it is nested in** — it resolves
that inner function's own internal scope. So `:errors(:idchain("..."))` is
legal (one pointer — `idchain` — at the argument level, one pointer —
`errors` — at the chain's own top level). Conversely, `:last():index(3)`
sitting side by side in the same chain is illegal (two pointers, same
level).

---

## 7. Grammar and Implementation

#### 7.1
The v3 grammar is `csvpath/references/reference_grammar_3.py`.

An LALR Lark grammar is required. LALR is required to support
`parse_interactive()`-based type-ahead.

Function names, the requirement for `name_three`, or not, and other factors are
grammatically neutral and enforced during parse tree interpretation.


#### 7.2
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
#### 7.3
- **`Function3`** (`csvpath/references/functions/function_3.py`) the base class
for real, behavior-having functions. (Note: `FunctionCall3` is the parse tree
object.)

- **`ReferenceFunctionFactory`** (`reference_function_factory_3.py`) is the
name-keyed registry for all functions. `add_function(cls)` allows for future
custom function registration.

### `ReferenceFinder3` ABC and results containers
#### 7.4
- **`ReferenceFinder3`** is an ABC taking `(*, csvpaths, ref: ReferenceParser3)`.
Using a reference has two stages:
- query
- resolve

The query stage is performed with the `query()` method. The result is a list
of path+uuid pairs, with two other fields for specific cases, as described
elsewhere.

The following resolve stage is performed with `resolve()`, and implies `query()`.
Resolve gives whole files or field values, in addition to path+uuid.

#### 7.5
Selected items from the list produced by `query()` may be resolved without
resolving the whole list originally returned.

#### 7.6
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

#### 7.7
`__eq__` compares all four fields (`path`+`uuid`+`data`+`identity`) — this is
what `ReferenceResults3.deduplicated()` uses to collapse true duplicates.
Different results may be returned after `resolve()` than would after only
`query()`.


### The finders
#### 7.8
`FilesReferenceFinder3`, `CsvpathsReferenceFinder3`, `ResultsReferenceFinder3`
find results based on a ReferenceParser which represents a reference string.

**What a reference results object `path` actually holds**

#### 7.9
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






