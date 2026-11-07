# Customizing the stand-ins

The managed identifier stand-ins will not suit every data set. A short
keyword can match inside a column name. A format your data uses may not be
one we included. Your compliance team may want a severity higher than
Macie's. A **project rulesbase** lets you change the stand-ins for your
project, without editing the Framework, and records what you changed.

## Turning it on

The project rulesbase is a directory, `rulesbase` by default, set in
`config.ini`:

```ini
[macie]
rulesbase = rulesbase
```

**Create `rulesbase/macie/` to opt in.** The Framework never creates it.
Once it exists, every wrapper load:

- writes `rulesbase/macie/packaged_managed_identifiers.json`, a copy of
  the packaged catalog, so you can see the stand-ins you are customizing.
  It is rewritten on each load and never read;
- reads your overrides from `rulesbase/macie/managed_identifiers.json`,
  if it exists, and merges them over the packaged catalog.

```
rulesbase/
  macie/
    managed_identifiers.json            your overrides
    packaged_managed_identifiers.json   the packaged catalog, for reference
```

## The overrides file

It holds only your changes. Everything you do not name comes from the
packaged catalog, so identifiers and fixes added in later releases still
reach you.

### Tightening a keyword list

Your data has a `cargo` column, and `BRAZIL_RG_NUMBER` reports 8 digit
cargo codes because Macie's keyword `rg` is inside `cargo`. Keep only the
long keyword:

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

### Raising a severity

```json
{
  "version": 1,
  "identifiers": {
    "LATITUDE_LONGITUDE": { "severity": "1:MEDIUM 2:HIGH" }
  }
}
```

### Adding a format

Brazil RG numbers from Minas Gerais are written `MG-12.345.678`. Add the
shape to the detector's formats:

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

The format notation: `#` a digit, `A` a letter, `X` a letter or digit,
`[...]` one of a set (ranges such as `A-C` allowed), `{n}` or `{m,n}`
after a symbol or set for a count. Any other letter goes in a set, as
`[M]` above. Spaces and punctuation stand for themselves.

## What you can change

| Section | You can | You cannot |
|---|---|---|
| `keyword_lists` | replace a list's `keywords`; add a new list | |
| `identifiers` | change `keyword_mode`, `keywords_from`, `distance`, `severity`, `partial` | change Macie's category or which detector an identifier uses; add identifiers |
| `detectors` | change the data the detector reads (for example `formats`, `exclusions`, `countries`) | add detectors |

Every entry may have a `why`: your note, kept with the merged catalog.

The packaged entries and their keys are in
`packaged_managed_identifiers.json`; the
[reference](managed-identifiers.md) lists each identifier's keyword list
and detector names.

Identifier names are Macie's, and a wrapper can only select those, so
there is nothing to gain from adding identifiers. To point one
identifier at its own keywords, add a list and set the identifier's
`keywords_from`:

```json
{
  "version": 1,
  "keyword_lists": { "our_dl": { "keywords": ["licence no"] } },
  "identifiers": { "UK_DRIVERS_LICENSE": { "keywords_from": "our_dl" } }
}
```

## Mistakes stop the load

Every override is checked before anything is converted: the sections and
keys, the merged catalog as a whole, and each changed detector, which is
built once so that a bad format fails here, not in a run.

```
MacieException: Project rulesbase rulesbase/macie/managed_identifiers.json
detectors.br_rg cannot override formts; it can override exclude_prefixes, exclusions, formats
```

## Seeing what was applied

The conversion report of every load lists the overrides it applied:

```json
"rulesbase": {
  "overrides_path": "rulesbase/macie/managed_identifiers.json",
  "applied": ["keyword_lists.br_rg"]
}
```

The merged catalog is the group's `assets/macie_catalog.json`, and each
group run copies it into its run directory (see
[reproducibility](reproducibility.md)).

## When changes take effect

When a group is loaded. A loaded group keeps the catalog it was loaded
with; reload the group to use a changed rulesbase. Appending a wrapper to
a group under a changed rulesbase is refused, since the group's other
csvpaths would detect differently than the new one.
