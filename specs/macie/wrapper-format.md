# CsvPath Macie wrapper format (draft, v1)

Macie has no single rules file. Its configuration is spread over several
API resources. The *wrapper* is the one JSON file the Framework defines to
hold all of it. It is the only Macie input that `add_named_paths_from_file()`
accepts.

A wrapper is produced in one of two ways:

- **Downloaded**: the Framework calls the Macie API (boto3 `macie2`) and
  S3, then writes the wrapper file. Loading is a separate step that reads
  that file. Download never transpiles; load never calls AWS.
- **Handcrafted**: a user writes the same structure by hand. Unusual, but
  supported. It needs only the required fields listed below.

Examples: `tests/macie/test_resources/wrappers/` (a downloaded job with
warnings, and the smallest handcrafted wrapper), and each normative pair's
wrapper under `tests/macie/test_resources/normative/`. The JSON Schema is
`csvpath/macie/schemas/csvpath-macie-wrapper-v1.json`; the cross-checks it
can't express are in `MacieWrapperLoader`.

## Principles

1. **AWS responses are kept verbatim.** Each Macie response sits unchanged
   under its own key, minus boto3's `ResponseMetadata`. Datetimes are
   written as UTC ISO 8601 strings (`2026-10-29T17:40:00Z`), which is the
   API's own wire format. An auditor can compare the file directly with AWS.
2. **Our additions sit beside the verbatim data, never inside it.** For
   example, an allow list's downloaded entries go in `contents`, next to
   the verbatim `settings`.
3. **Download records facts; transpile interprets them.** The download does
   not decide which findings filters apply or which identifiers we support.
   The transpiler decides that and says so in its conversion report.
4. **Problems are recorded, not just logged.** Anything that went wrong
   during download goes in `warnings`, so every later load and run can
   repeat it.

## Top level

| Key | Required | Meaning |
|---|---|---|
| `csvpath_macie` | yes | Format version, integer. `1`. This key is what marks a JSON file as a Macie wrapper. |
| `source` | yes | Where the wrapper came from. |
| `selection` | yes | Which identifiers and allow lists are in use, in one normalized form. |
| `managedDataIdentifiers` | yes | The resolved managed identifier IDs, plus the AWS snapshot if downloaded. |
| `customDataIdentifiers` | no | Verbatim `GetCustomDataIdentifier` responses. Default `[]`. |
| `allowLists` | no | Allow-list settings plus contents. Default `[]`. |
| `findingsFilters` | no | Verbatim `GetFindingsFilter` responses. Default `[]`. |
| `aws` | no | Verbatim job or template response the selection came from. |
| `warnings` | no | Download-time problems. Default `[]`. |

Unknown top-level keys are an error, so that typos fail fast.

## `source`

```json
"source": {
  "origin": "job",
  "account_id": "123456789012",
  "region": "us-east-1",
  "downloaded_at": "2026-10-29T17:40:00Z",
  "job_id": "3ce05dbb7ec5505def334104bf1b3bca"
}
```

- `origin`: `job`, `template` or `handcrafted`. Required.
- `job_id`: required when `origin` is `job`.
- `template_id`: required when `origin` is `template`.
- `account_id`, `region`, `downloaded_at`: required unless `handcrafted`.
  `downloaded_at` is the UTC time the download finished. We record *when*,
  not *who*: the account owner's own audit trail (CloudTrail) answers who.

## `selection`

The job's and the template's settings, reduced to one shape. The transpiler
reads only this, never `aws`.

```json
"selection": {
  "managedDataIdentifierSelector": "INCLUDE",
  "managedDataIdentifierIds": ["CREDIT_CARD_NUMBER", "USA_SOCIAL_SECURITY_NUMBER"],
  "excludedManagedDataIdentifierIds": [],
  "customDataIdentifierIds": ["..."],
  "allowListIds": ["..."]
}
```

How each origin maps onto this shape:

| Origin | `managedDataIdentifierSelector` | `managedDataIdentifierIds` | `excludedManagedDataIdentifierIds` |
|---|---|---|---|
| job, `INCLUDE` | `INCLUDE` | job's ids | `[]` |
| job, `EXCLUDE` | `EXCLUDE` | `[]` | job's ids |
| job, `ALL` / `NONE` / `RECOMMENDED` / null | as given; null becomes `RECOMMENDED` | `[]` | `[]` |
| template | `RECOMMENDED` | `includes.managedDataIdentifierIds` | `excludes.managedDataIdentifierIds` |

A template uses "the automated-discovery recommended set, plus includes,
minus excludes". That is why it maps to `RECOMMENDED` with both lists.
Note that the recommended set for **automated discovery** is not the same
list as the recommended set for **jobs**. Both are published only in the
docs, not through the API, so the Framework ships both lists as dated
assets (see `managedDataIdentifiers.resolution`).

Every id in `customDataIdentifierIds` and `allowListIds` must have a
matching entry in `customDataIdentifiers` / `allowLists`. A missing entry
is an error at load time.

## `managedDataIdentifiers`

```json
"managedDataIdentifiers": {
  "resolved": ["CREDIT_CARD_NUMBER", "USA_SOCIAL_SECURITY_NUMBER"],
  "resolution": {
    "method": "selector",
    "recommended_list": null
  },
  "available": [ { "category": "FINANCIAL_INFORMATION", "id": "CREDIT_CARD_NUMBER" } ]
}
```

- `resolved` (required): the concrete list of managed identifier IDs the
  selection stands for **at download time**. This matters because `ALL`,
  `EXCLUDE` and `RECOMMENDED` follow AWS's list as it changes. The wrapper
  pins it.
- `resolution.recommended_list`: when the selector is `RECOMMENDED`, the
  name and date of the Framework asset used, e.g.
  `"jobs-recommended@2026-10-29"`. Null otherwise.
- `available`: verbatim `ListManagedDataIdentifiers` items (all pages
  merged). Present when downloaded. It lets a load report "AWS offered N
  identifiers that the Framework has no stand-in for".

The download does not judge which resolved IDs we support. The transpiler
does that against the user's `rulesbase`.

## `customDataIdentifiers`

A list of verbatim `GetCustomDataIdentifier` responses. Soft-deleted
identifiers (`"deleted": true`) are kept when the selection uses them,
because Macie jobs keep using them too.

## `allowLists`

```json
{
  "settings": { "...verbatim GetAllowList response..." },
  "contents": {
    "status": "OK",
    "entries": ["Akua Mansa", "425-555-0100"],
    "sha256": "…",
    "error": null
  }
}
```

- `settings` (required): verbatim `GetAllowList`. That includes Macie's own
  `status.code` (e.g. `S3_OBJECT_ACCESS_DENIED`), which is about whether
  **Macie** can read the list.
- `contents` (required for `s3WordsList` lists, absent for `regex` lists):
  - `status`: whether the **Framework** could read the S3 object: `OK`,
    `ACCESS_DENIED`, `NOT_FOUND`, `EMPTY` or `ERROR`.
  - `entries`: the lines as read, blank lines dropped. Otherwise unchanged:
    no lowercasing. Case-insensitive matching is the transpiler's job.
  - `sha256`: hex digest of the S3 object's raw bytes.
  - `error`: message when `status` is not `OK`.

If `contents.status` is not `OK`, the download still writes the wrapper
and adds a warning. The transpiler generates the rules without that list,
and every run report says the list was missing.

Entries can be real names, phone numbers, etc. A wrapper should be treated
as at least as sensitive as the allow list it was copied from.

## `findingsFilters`

A list of verbatim `GetFindingsFilter` responses, in `position` order. All
are downloaded. The transpiler applies the conditions it can map (on
`severity.description`, `sensitiveData.category`,
`sensitiveData.detections.type`, `customDataIdentifiers.detections.*`) and
lists the rest in its conversion report as recorded but not applied.

## `aws`

```json
"aws": { "classificationJob": { "...verbatim DescribeClassificationJob..." } }
```

or `{ "sensitivityInspectionTemplate": { ... } }`. Kept for audit and as
metadata only. Job scoping (`s3JobDefinition`, `samplingPercentage`,
schedules) has no effect on transpiling.

## `warnings`

```json
"warnings": [
  { "code": "ALLOW_LIST_UNREADABLE", "subject": "<allow list id>",
    "message": "s3:GetObject denied on s3://acme-macie-lists/public-names.txt" }
]
```

Codes so far: `ALLOW_LIST_UNREADABLE`, `MACIE_ALLOW_LIST_STATUS`
(Macie itself reports a non-`OK` status), `CDI_DELETED_BUT_SELECTED`.

## Load-time checks (fail fast)

- `csvpath_macie` is present and is a supported version.
- Required keys are present, and there are no unknown top-level keys.
- `source.origin` is valid and has its required id.
- Selected ids and entries match one to one: every selected custom
  identifier and allow-list id has an entry, and every entry is selected.
- No duplicate ids anywhere.
- The selector agrees with `resolved`: `NONE` resolves to nothing,
  `INCLUDE` to exactly its ids, `EXCLUDE`/`ALL`/`RECOMMENDED` never
  resolve an excluded id, and only `RECOMMENDED` names a
  `recommended_list` (and must). A template's selector is `RECOMMENDED`.
- A text allow list with status `OK` has entries and a `sha256`; with any
  other status it has no entries.
- Each custom identifier has a non-empty `regex`.
- Each allow list has exactly one of `criteria.regex` /
  `criteria.s3WordsList`, and `contents` is present for an `s3WordsList`.

## Decided

1. **One wrapper per job, one named-paths group per wrapper.** A 1-to-1
   operation, same as ODCS. (David, 2026-10-29)
2. **No `downloaded_by`.** Capture when, not who. (David, 2026-10-29)
3. **File suffix `.macie.json`.** Directory loads pick up only
   `*.macie.json`. A file with the suffix must still carry the
   `csvpath_macie` key, and a file without it is an error, not a skip.
   (David, 2026-10-29)
