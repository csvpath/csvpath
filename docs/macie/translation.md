# What gets translated

One Macie job (or automated-discovery template) becomes one csvpath. Each
custom identifier, managed identifier and allow list becomes one Macie
function call in it:

```
$[1*][
    macie_allow_regex.nocontrib("<allow list>", /<regex>/)
    macie_allow_words.nocontrib("<allow list>", load_list("<allow list id>"))
    macie_cdi("<name>", "<ARN>", /<regex>/, "<keywords>", "<ignore words>", <distance>, "<severity>")
    macie_mdi("<managed id>", "<category>", "<detector>", "<keyword mode>", "<keywords>", <distance>, "<severity>")
    last.nocontrib() -> macie_report()
]
```

Allow lists come first, since they register state the identifiers after
them use. Custom identifiers come next, then managed identifiers in the
order Macie resolved them. Every argument is visible in the csvpath, so
you can read exactly what will be checked.

## Summary

| Macie | CsvPath | Notes |
|---|---|---|
| Custom data identifier | `macie_cdi(...)` | regex, keywords, ignore words, `maximumMatchDistance`, severity levels |
| Managed data identifier with a stand-in | `macie_mdi(...)` | 148 of them; see the [reference](managed-identifiers.md) |
| Managed data identifier without one | reported, not translated | `NAME`, `ADDRESS`, `SPAIN_SOCIAL_SECURITY_NUMBER` (planned), 15 driver's license countries |
| Regex allow list | `macie_allow_regex(...)` | |
| Text (S3 words) allow list | `macie_allow_words(...)` with `load_list()` | entries stored in the group's assets |
| Text allow list unreadable at download | reported, not translated | its identifiers still run, without it |
| Findings filters | reported, not applied | they act on findings after detection |
| Job scoping, sampling, schedules | not used | metadata only |
| Download warnings | reported | every one, in the conversion report |

## Custom data identifiers

For each cell of each line, for each non-overlapping match of the regex,
in order:

1. **Keywords** (skipped when there are none). The match counts if the
   column header contains a keyword, or a keyword appears earlier in the
   same cell with at most `maximumMatchDistance` characters from the end
   of the keyword to the end of the match. Keywords are not case
   sensitive. A keyword with spaces also matches with the spaces removed
   or replaced by `_` or `-`, so `employee id` matches the header
   `employee_id`.
2. **Ignore words.** The match is dropped if it contains an ignore word
   (case sensitive).
3. **Allow lists.** The match is dropped if its text equals a text
   allow-list entry (ignoring case) or fully matches an allow-list regex.
4. Otherwise it is an **occurrence**.

Regexes are matched as Macie matches them: case sensitive unless the
pattern says `(?i)`, no implicit anchors or word boundaries, `\d`, `\w`
and `\s` ASCII only. Mid-pattern inline flags such as `ab(?i)cd`, which
Python's `re` rejects, are rewritten to their scoped form.

## Managed data identifiers

AWS does not publish its detectors' code. Each of our **stand-ins** is a
catalog entry and a detector:

- the **detector** finds candidates: a format, and a check digit or
  other structural check where the issuer publishes one (Luhn for cards,
  mod 97 for IBANs, the Spanish DNI letter, and so on);
- the **keyword mode** says whether a keyword is needed: `required` (in
  the column name, or in the same cell within 30 characters before or
  after the occurrence), `absent` (only when no keyword is there, as for
  `CREDIT_CARD_NUMBER_(NO_KEYWORD)`), or `none`;
- the **keywords** and **severity** are Macie's published ones.

Each entry records the AWS page it came from and the date retrieved, so
the catalog can be checked against AWS as its documentation changes.

### Fidelity tiers

| Tier | Meaning |
|---|---|
| **A** | Macie documents the rule (or names the standard), and the stand-in implements it: the format and any check digit are known. |
| **B** | Macie publishes the keywords and little else. The format and checks are ours, from the issuer's published rules or, where there are none, from reliable secondary sources. |

### Partial stand-ins

A stand-in that detects less than Macie says Macie detects is marked
**partial**, and every conversion that uses it says so in its report:

```json
{ "feature": "managedDataIdentifier.partial",
  "reason": "Only GS1 and HIBCC UDIs are detected, not ICCBBA ISBT 128 UDIs" }
```

The partial stand-ins are listed in [limitations](limitations.md).

## Severity

Custom identifiers use the job's severity levels, written as
`"1:LOW 5:MEDIUM 10:HIGH"`: the severity for 1 to 4 occurrences in a file
is LOW, 5 to 9 MEDIUM, 10 or more HIGH. With no levels in the wrapper the
default is Macie's, `"1:MEDIUM"`. Managed identifiers use Macie's
published severity table for their type, for example `1:HIGH` for card
numbers and `1:LOW 2:MEDIUM 100:HIGH` for phone numbers.

## The conversion report

Every load writes `<wrapper>.report.json` beside the wrapper in the group
home. For example (illustrative values):

```json
{
  "source_path": "hr-employee-ids.macie.json",
  "name": "hr-employee-ids",
  "origin": "job",
  "job_id": "5d0c4a1e8b7f6e5d4c3b2a1f0e9d8c7b",
  "template_id": null,
  "account_id": "123456789012",
  "region": "us-east-1",
  "downloaded_at": "2026-10-29T17:40:00Z",
  "lists": [{ "name": "c0n7r4a1c7o9r5s3a6l0lw", "entries": 3 }],
  "skipped": [
    { "object": "hr-employee-ids",
      "location": "managedDataIdentifiers.resolved[2]",
      "feature": "managedDataIdentifier",
      "reason": "Managed data identifier NAME is not translated yet" }
  ],
  "rulesbase": { "overrides_path": null, "applied": [] }
}
```

`skipped` lists everything not translated, or translated only in part.
`lists` gives each allow list's id and entry count, never its entries.
`rulesbase` names any project customizations applied (see
[customizing](customizing.md)).

## What stops a conversion

Some things cannot be translated without changing what is detected. They
stop the load with an error instead of being skipped:

- a keyword, ignore word or name containing `"`, or a keyword or ignore
  word containing `|`;
- a regex that does not translate and compile;
- a malformed ARN;
- a job name that cannot be a csvpath id or group name, with no usable
  file name to fall back on (names are letters, digits, `.`, `_` and `-`);
- an invalid wrapper (a missing required key, an unknown key, selected
  ids without entries, and so on).

This is stricter than the ODCS converter on purpose: a wrong ODCS
translation is a validation error, but a wrong Macie translation can miss
sensitive data.
