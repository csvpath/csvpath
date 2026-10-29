#!/usr/bin/env python3
"""Regenerates the reference-v3 test corpus under tests/corpus/data/ from
the asset list in tests/corpus/assets.yaml.

Drives the real CsvPath Framework registration/run code paths
(FileManager.add_named_file, PathsManager.add_named_paths,
CsvPaths.fast_forward_paths) rather than hand-authoring manifests, so every
directory name, manifest schema, and timestamp is exactly what production
code writes. Historical spread comes from csvpath.util.date_util.DateUtility
(OFFSET_DAYS/OFFSET_MONTHS/OFFSET_YEARS), which both the run-directory namer
(RunHomeMaker) and the metadata timestamp writer (Metadata) already consult
-- so a version/load/run's directory name and its own manifest "time" field
are generated already consistent, with no retrofit/rename pass needed.

Every file registration, named-paths load, and run is collected into one
flat list of events and executed in true chronological order (oldest
offset_days first), not grouped by kind -- so a run with an early
offset_days only ever sees whichever named-paths/named-file versions had
already been "created" by that point in simulated time, the same way a real
system's history would have unfolded, rather than every run seeing the
group's final, most-mutated version regardless of how far back it claims to
be.

Named-paths groups accumulate for real: each version after a group's first
load is a genuine PathsManager.add_named_paths(paths=[...], append=True)
call that adds one more trivial statement onto whatever content the group
already had (confirmed live: append=True rewrites the group file as
existing-content + new-content), not an independent mutation of the
pristine original. Named-files groups have no equivalent append mode, so
repeat versions there are still independent mutated copies (CSV: duplicate
the last row) under their own scratch subdirectory.

Note: template date tokens (":year", ":month_name", etc., in
TemplateUtility.transform_template) read real wall-clock time directly, NOT
DateUtility -- they are unaffected by the offsets here. Template-preserving
a source file's own folder structure uses positional tokens (":0", ":1",
...) instead, which is why acme_invoices in assets.yaml has no template at
all yet despite its source tree already having a real year/month structure
-- positional tokens are indexed against whatever path string is passed to
add_named_file(), which makes them fragile to the exact repo-relative depth
of the source path. Left for a future pass once the corpus's own asset
layout settles down.

Usage:
    poetry run python tests/corpus/generate.py

Safe to re-run: wipes and rebuilds tests/corpus/data/ from scratch every
time, so the asset list is the only thing you need to edit to grow the
corpus.
"""
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = Path(__file__).resolve().parent
DATA_DIR = CORPUS_DIR / "data"
SCRATCH_DIR = CORPUS_DIR / ".scratch"
ASSETS_PATH = CORPUS_DIR / "assets.yaml"
CONFIG_PATH = CORPUS_DIR / "config" / "config.ini"

#
# the config is chosen in main(), not on import, so a test can import
# build_events()/run_events() without switching its whole process to the
# corpus config
#
sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from csvpath import CsvPaths  # noqa: E402
from csvpath.util.date_util import DateUtility  # noqa: E402


def reset_data_dir() -> None:
    for sub in (
        "inputs/named_files",
        "inputs/named_paths",
        "archive",
        "logs",
        "cache",
        "transfers",
    ):
        p = DATA_DIR / sub
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)
    if SCRATCH_DIR.exists():
        shutil.rmtree(SCRATCH_DIR)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)


def set_now(offset_days: int) -> None:
    DateUtility.OFFSET_DAYS = offset_days
    DateUtility.OFFSET_MONTHS = 0
    DateUtility.OFFSET_YEARS = 0


def reset_now() -> None:
    DateUtility.OFFSET_DAYS = 0
    DateUtility.OFFSET_MONTHS = 0
    DateUtility.OFFSET_YEARS = 0


def mutate_csv(source: Path, dest: Path, count: int) -> None:
    """forces a new content fingerprint by duplicating the source's own
    last line `count - 1` times -- stays genuinely valid tabular data
    (same column structure), just more rows than the original. Scaling
    the duplicate count by `count` (rather than always adding exactly
    one row) matters: every use mutates from the PRISTINE original, not
    cumulatively from the previous mutation (no append-mode equivalent
    exists for named-files, unlike named-paths), so a fixed single-row
    addition would produce byte-identical output -- and therefore the
    SAME fingerprint -- on every call, silently deduping every version
    after the second down to just one (confirmed live before relying on
    this fix: orders had 5 versions scheduled in assets.yaml but only 2
    distinct fingerprints actually registered)."""
    text = source.read_text()
    if not text:
        shutil.copy(source, dest)
        return
    if not text.endswith("\n"):
        text += "\n"
    lines = text.splitlines(keepends=True)
    last = lines[-1]
    dest.write_text(text + last * (count - 1))


def append_statement(marker: str) -> str:
    """one more trivial, always-valid csvpath statement -- passed to
    PathsManager.add_named_paths(paths=[...], append=True) so a repeat
    "version" of a named-paths group genuinely accumulates onto whatever
    content the group already had, rather than independently mutating the
    pristine original."""
    return (
        f"~ name: generated check {marker}\n"
        "  description: appended by the corpus generator to simulate a\n"
        "    named-paths group gaining an additional check over time.\n"
        "~\n\n"
        "$[*][\n"
        "    yes()\n"
        "]"
    )


def versioned_source(
    group_name: str, source_rel: str, use_counts: dict, *, scratch_dir: Path
) -> Path:
    """returns the real source path for a named_files group's FIRST use of
    `source_rel`, or a mutated scratch copy -- under its OWN numbered
    subdirectory, with the ORIGINAL basename preserved -- for every
    subsequent use. CsvPath Framework dedupes identical content and
    silently drops a repeat registration otherwise (confirmed live before
    relying on this), so a genuinely distinct fingerprint is required;
    keeping the original basename (rather than folding the group name/
    count into the filename itself) matters because the registration's
    own file_home directory is named after it -- a mutated copy should
    look like an ordinary later arrival of the same file, not generator
    scratch output leaking into the corpus.

    Returned relative to the current working directory (expected to be
    REPO_ROOT, per this module's own Usage docstring), not absolute --
    FileManager records whatever path string it is given verbatim as
    "origin_path" in the manifest, and an absolute path there would bake
    this machine's own home directory into a file meant to be committed
    and shared."""
    source = REPO_ROOT / source_rel
    key = (group_name, source_rel)
    use_counts[key] = use_counts.get(key, 0) + 1
    count = use_counts[key]
    if count == 1:
        result = source
    else:
        scratch_subdir = scratch_dir / f"{group_name}__{count}"
        scratch_subdir.mkdir(parents=True, exist_ok=True)
        mutated = scratch_subdir / source.name
        if source.suffix.lower() == ".csv":
            mutate_csv(source, mutated, count=count)
        else:
            # no mutation strategy for this extension (e.g. .xlsx) --
            # repeats of a non-CSV source would just silently dedupe;
            # the asset list is expected to only use each non-CSV source
            # once per group until a mutator exists for it.
            shutil.copy(source, mutated)
        result = mutated
    return Path(os.path.relpath(result, start=Path.cwd()))


def build_events(assets: dict) -> list[tuple[int, str, dict]]:
    """flattens the whole asset list into one (offset_days, kind, payload)
    list -- the caller sorts this by offset_days and executes in order, so
    every event genuinely only ever sees what would already exist at that
    point in the corpus's own simulated history."""
    events: list[tuple[int, str, dict]] = []
    for group in assets.get("named_files", []) or []:
        name = group["name"]
        template = group.get("template")
        for version in group["versions"]:
            events.append(
                (
                    version["offset_days"],
                    "file",
                    {"name": name, "source": version["source"], "template": template},
                )
            )
    for failure in assets.get("named_file_failures", []) or []:
        events.append(
            (
                failure["offset_days"],
                "file_failure",
                {"name": failure["name"], "bad_source": failure["bad_source"]},
            )
        )
    for group in assets.get("named_paths", []) or []:
        name = group["name"]
        source = group["source"]
        for version in group["versions"]:
            events.append(
                (version["offset_days"], "paths", {"name": name, "source": source})
            )
    for run_group in assets.get("results", []) or []:
        paths_name = run_group["paths_name"]
        against_file = run_group["against_file"]
        for run in run_group["runs"]:
            events.append(
                (
                    run["offset_days"],
                    "run",
                    {"paths_name": paths_name, "against_file": against_file},
                )
            )
    events.sort(key=lambda e: e[0])
    return events


def run_events(
    csvpaths: CsvPaths,
    events: list[tuple[int, str, dict]],
    *,
    scratch_dir: Path = SCRATCH_DIR,
) -> None:
    """executes the events in order. scratch_dir holds the mutated copies
    of repeat named-file sources; a test passes its own temp directory."""
    if not isinstance(scratch_dir, Path):
        raise TypeError("scratch_dir must be a Path")
    file_use_counts: dict = {}
    paths_use_counts: dict = {}
    for offset_days, kind, payload in events:
        set_now(offset_days)
        if kind == "file":
            src = versioned_source(
                payload["name"],
                payload["source"],
                file_use_counts,
                scratch_dir=scratch_dir,
            )
            csvpaths.file_manager.add_named_file(
                name=payload["name"], path=str(src), template=payload["template"]
            )
        elif kind == "file_failure":
            # add_named_file() raises ValueError for an empty/None path --
            # confirmed this is the real trigger for a "Registration
            # failed" ledger entry (a merely-nonexistent path is NOT:
            # can_load() only checks HTTP/local-file policy flags, not
            # existence, so it silently matches zero files instead).
            # The ledger entry is written before the raise, so catching
            # here is safe -- mirrors the real test's
            # `with pytest.raises(ValueError):` but as production-safe
            # generator code.
            try:
                csvpaths.file_manager.add_named_file(
                    name=payload["name"],
                    path=payload["bad_source"],
                )
            except ValueError:
                pass
        elif kind == "paths":
            name = payload["name"]
            paths_use_counts[name] = paths_use_counts.get(name, 0) + 1
            count = paths_use_counts[name]
            if count == 1:
                csvpaths.paths_manager.add_named_paths(
                    name=name, from_file=payload["source"]
                )
            else:
                # real accumulation: this appends one more trivial statement
                # onto whatever the group's content already was, rather than
                # mutating the pristine original independently each time
                # (confirmed live: add_named_paths(append=True) rewrites the
                # group file as existing-content + new-content).
                csvpaths.paths_manager.add_named_paths(
                    name=name, paths=[append_statement(str(count))], append=True
                )
        elif kind == "run":
            csvpaths.fast_forward_paths(
                pathsname=payload["paths_name"], filename=payload["against_file"]
            )
        else:
            raise ValueError(f"Unknown event kind: {kind}")


def main() -> None:
    os.environ["CSVPATH_CONFIG_PATH"] = str(CONFIG_PATH)
    reset_data_dir()
    assets = yaml.safe_load(ASSETS_PATH.read_text())
    events = build_events(assets)
    csvpaths = CsvPaths()
    try:
        run_events(csvpaths, events)
    finally:
        reset_now()
    shutil.rmtree(SCRATCH_DIR, ignore_errors=True)
    print(f"Corpus regenerated under {DATA_DIR} ({len(events)} events)")


if __name__ == "__main__":
    main()
