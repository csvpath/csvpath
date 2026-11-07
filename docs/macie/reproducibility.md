# Reproducibility

**For an auditable, reproducible compliance record, run Macie rules in a
named-paths group.** A group run keeps a point-in-time copy of every Macie
input next to its results, so it can be replicated with exactly the rules
it used. A standalone `CsvPath` run is for fast checks.

## What a group keeps

When a wrapper is loaded, the group home holds:

| File | What |
|---|---|
| `<wrapper>.macie.json` | the wrapper, byte for byte |
| `<wrapper>.macie.json.report.json` | the conversion report |
| `group.csvpaths` | the generated csvpath: every identifier's regex, keywords, distance and severity, and the limits |
| `assets/<list id>.txt` | each text allow list |
| `assets/macie_catalog.json` | the managed identifier catalog the wrapper was converted with |

**The catalog snapshot** matters because the managed identifier stand-ins
change: new releases add identifiers and fix detectors, and a project can
[customize](customizing.md) them. A group run reads only its own snapshot.
Upgrading the Framework or editing the project rulesbase changes nothing
for a loaded group until it is reloaded. A group whose snapshot is
missing does not run: it fails with "reload the group".

## What each run keeps

At the start of a group run, the run copies the group's Macie inputs into
its run directory, under `_extra_data`, the Framework's place for
non-standard inputs, background and side-effects:

```
archive/hr_ids/2026-11-07_22-25-11/
  _extra_data/macie/
    hr-contractor-allow.macie.json
    hr-contractor-allow.macie.json.report.json
    macie_catalog.json
    lists/c0n7r4a1c7o9r5s3a6l0lw.txt
    inputs.json
  hr-contractor-allow/
    data.csv  errors.json  macie.txt  vars.json  manifest.json  meta.json
```

`inputs.json` records the group and each file's sha256:

```json
{
  "group": "hr_ids",
  "files": {
    "hr-contractor-allow.macie.json": "9f2c...",
    "hr-contractor-allow.macie.json.report.json": "41ab...",
    "lists/c0n7r4a1c7o9r5s3a6l0lw.txt": "c3d0...",
    "macie_catalog.json": "77e1..."
  }
}
```

With the run's copy of its inputs and its data file, the run can be
repeated, on the same Framework version, and its findings compared.

When a group holds more than one Macie csvpath, the first copies the
inputs and the others check them against `inputs.json`. If an input
changed during the run, the run fails rather than mixing rules.

## Rules that protect a group

Appending to a group must not change what its existing csvpaths detect.
These are refused, before anything is written:

- a Macie csvpath whose id is already used in the group;
- an allow list whose id is in the group with different entries;
- a wrapper converted with a different catalog than the group's (the
  Framework was upgraded, or the project rulesbase changed, since the
  group was loaded).

Each says what to do: reload the group without `append`, or give the list
a new id.

## Standalone runs

A converted csvpath also runs on its own, with `CsvPath`, outside any
group. That is useful in API backends and pipeline checks, where speed
matters and a full record does not. A standalone run reads the project
rulesbase (or the packaged catalog), copies nothing, and ends its `macie`
stream with:

```
macie: standalone run, not a reproducible record; run in a named-paths group for an auditable one
```

## What is not yet versioned

The Macie inputs above are copied per run. Other group configuration (for
example a group's `definition.json`) is not yet versioned per run in the
Framework generally. That is a known gap, outside the Macie work.
