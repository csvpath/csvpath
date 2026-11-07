# Project rulesbase for the Macie stand-ins — design (DRAFT, for David)

Status: agreed 2026-11-07 (David: P1 yes; P2b in `_extra_data`, the place
for non-standard inputs, background and side-effects; P2c with standalone
runs valued for fast API and pipeline checks). Worklist item 4a. PR 1
(merge and validation) built: `RulesbaseOverrides`,
`ManagedCatalog.load(overrides_path=...)`, and `CONFIG_KEYS` on every
detector class, the keys an override may change. PR 2 (load and snapshot) built:
`ProjectRulesbase`, `MacieGroupLoader.store_assets()`, the group's
`assets/macie_catalog.json`, and `MacieRun` reading only that in a group
run. One refinement in PR 2: the project opts in by creating
`<rulesbase>/macie/`. We never create it, so a project that never
customizes gets no new directory; once it exists, each load refreshes the
reference copy in it. Identifier and keyword list overrides are written
into the generated csvpath at conversion; the run reads detector data
from the snapshot, so both come from the one merged catalog.

## Why now

The stand-ins have known false positive and false negative risks (the
worklist's "Ask road-testers about" list): short keywords such as `rg`,
`cep` and `med` matching inside words, keywords that need their accents,
formats that are ours. The first question a partner will ask is "how do I
tune this?" Today the only answer is the converter's `catalog=` argument,
which a user loading a group never sees.

## Worked examples

### 1. Tightening a keyword list

A bank's data has a `cargo` column, and `BRAZIL_RG_NUMBER` reports 8 digit
cargo codes because `rg` is inside `cargo`. The bank keeps only the long
keyword. Its project file `rulesbase/macie/managed_identifiers.json`:

```json
{
  "version": 1,
  "keyword_lists": {
    "br_rg": {
      "keywords": ["registro geral"],
      "why": "rg matches our cargo column (ticket DATA-412)"
    }
  }
}
```

Everything not named here comes from the packaged catalog. On the next
load:

```
$ ... paths_manager.add_named_paths_from_file(name="kyc", file_path="kyc.macie.json")
macie: using project rulesbase rulesbase/macie/managed_identifiers.json
macie:   keyword_lists.br_rg overrides the packaged entry
```

### 2. A severity the compliance team wants higher

```json
{
  "version": 1,
  "identifiers": {
    "LATITUDE_LONGITUDE": { "severity": "1:MEDIUM 2:HIGH" }
  }
}
```

An identifier override is merged key by key over the packaged entry, so
the user writes only what they change.

### 3. A format we don't have

Brazil RG numbers from Minas Gerais (`MG-12.345.678`):

```json
{
  "version": 1,
  "detectors": {
    "br_rg": {
      "formats": ["##.###.###-[0-9X]", "#{8}-[0-9X]", "#{8}[0-9X]",
                  "[M][G]-##.###.###"]
    }
  }
}
```

A detector override replaces the named fields (here `formats`) and keeps
the rest. Detector names are fixed: each maps to code in `DETECTORS`, so an
override can change a detector's data but not add a new detector.

### 4. A mistake is loud

```json
{ "version": 1, "identifiers": { "LATITUDE_LONGITUDE": { "severity": "lots" } } }
```

```
MacieException: Project rulesbase rulesbase/macie/managed_identifiers.json:
LATITUDE_LONGITUDE severity 'lots' is not occurrences:LEVEL pairs
```

The merged catalog goes through the same validation the packaged catalog
does, before any conversion. Macie fails loudly (legal stakes), so a bad
customization stops the load, never falls back silently.

### 5. What a run used is on record

After example 1, the group home holds the catalog the group was loaded
with:

```
named_paths/kyc/
  group.csvpaths
  kyc.macie.json
  kyc.macie.json.report.json      <- also lists the overrides applied
  assets/
    macie_catalog.json            <- the merged catalog, as loaded
```

A run of the group reads `assets/macie_catalog.json`, not the project
file, the same rule `load_list()` follows for allow lists: in a group run
the asset must be the group's, no fallback. Editing the project rulesbase
changes nothing until the group is reloaded, and a past run's findings can
always be traced to the exact rules that produced them.

## Proposals to agree

**P1. An overrides file, not a full copy.** David's notes suggest copying
the packaged catalog into the project and never overwriting it. The
problem: the catalog grows with every release (135 to 148 identifiers this
week). A project that copied it last month would silently miss this
month's identifiers and fixes, and a diff between the two is hard to read.
An overrides file holds only the user's changes, so upgrades flow through
and the customizations are visible at a glance. To keep the notes' intent,
that users can see and start from our rules, the load also writes the
packaged catalog, read-only in spirit, beside it as
`rulesbase/macie/packaged_managed_identifiers.json`, rewritten on each
load and never read back. Merge granularity: one `keyword_lists` or
`detectors` entry's named fields, one `identifiers` entry's named keys.

**P2. The merged catalog is snapshotted into the group on load** (example
5), and a group run reads only the snapshot. Outside a group (a plain
`CsvPath` run of a converted csvpath), the run reads the project
rulesbase if there is one, else the packaged catalog.

**P2b. A group run copies its Macie inputs into the run dir.** For
auditable, reproducible compliance a Macie csvpath must run in a
named-paths group: only a group run leaves a point-in-time copy of every
input in named-results, so the run can be replicated with the exact rules
it used (David's notes, item 4). At the start of a group run the Macie
functions copy the group's Macie inputs into the run's `_extra_data`, the
Framework's place for non-standard inputs, background and side-effects,
beside its `extra.json`:

```
archive/kyc/2026-11-07_10-15-00/
  manifest.json
  _extra_data/
    extra.json                      <- the Framework's, unchanged
    macie/
      kyc.macie.json                <- the wrapper, as loaded
      kyc.macie.json.report.json    <- the conversion report
      macie_catalog.json            <- the catalog snapshot the run used
      lists/
        approved_test_ids.txt       <- each text allow list
      inputs.json                   <- each file's sha256, and the group
                                       it came from
  kyc/                              <- the instance dir: data.csv,
    ...                                errors.json, vars.json (findings),
                                       printouts.txt, as today
```

Copied once per run, by the first Macie csvpath that runs; a second Macie
csvpath in the same group run finds the files there and checks their
hashes, failing loudly if they differ. Versioning a group's other
configuration is a wider Framework gap, accepted for now and out of scope
here; P2 and P2b cover the Macie inputs without depending on it.

**P2c. A standalone run says what it is.** A plain `CsvPath` run of a
Macie csvpath is useful in its own right: in API backends and pipeline
checks where speed matters and a reproducible record and full output do
not (David, 2026-11-07). It is not an error. It prints one line on the
`macie` stream at the end of the run:

```
macie: standalone run, not a reproducible record; run in a named-paths group for an auditable one
```

and nothing is copied anywhere.

**P3. Where the project rulesbase is:** `config.ini [macie] rulesbase`, a
directory, default `rulesbase` relative to the working directory, like the
other project paths in config.ini. The file inside is
`macie/managed_identifiers.json`. No file means no overrides: the packaged
catalog is used as is. The directory is never created unless the load
writes the packaged reference copy (P1).

**P4. `common.json` is deferred.** The notes' third level, rules shared
with other systems such as Purview, has no second rule system to share
with yet. The override file format leaves room for it (a `version` and
named sections) without building it now. Into the deferred list.

**P5. Out of scope for this step:** adding new detectors or new identifier
names (identifiers are Macie's names, and a wrapper can only select those);
per-group overrides (one project rulesbase for all groups); the converter's
per-identifier detail caps (`macie_cdi`'s 8th argument), which can come
later as one more identifier key.

## Tests

- Merge: each section's granularity; unknown section or key refused;
  overriding a detector or identifier that doesn't exist refused; the
  merged catalog validated.
- Load: no project file means the packaged catalog; the reference copy is
  written; the snapshot is in the group's assets; the report lists the
  overrides.
- Run: a group run reads the snapshot, even after the project file
  changes; outside a group, the project file, then the packaged catalog.
- Run dir (P2b): a group run's `_extra_data/macie/` holds the wrapper,
  report, catalog snapshot, lists and `inputs.json` with matching hashes;
  two Macie csvpaths in one run copy once; a changed file fails loudly.
- Standalone (P2c): the one line is printed; nothing is written.
- A normative pair loaded with an override (example 1), and a test that
  the packaged pairs are unchanged when there is no project file.

## PR plan

1. Merge and validation in `ManagedCatalog` (no I/O beyond reading), with
   unit tests.
2. Load: find the project file, write the reference copy, snapshot into
   the group, report the overrides; the run reads the snapshot. A normative
   pair.
3. Docs: the user-facing page for customizing the stand-ins (feeds the
   first docs draft).
