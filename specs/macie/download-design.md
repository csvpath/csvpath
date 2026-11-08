# Downloading a Macie wrapper — design (DRAFT, for David)

Status: proposal, 2026-11-08. Worklist item 7. Nothing built yet.

The wrapper format (`wrapper-format.md`) was designed for this from the
start: one file holding a Macie job's (or automated-discovery template's)
whole setup, the AWS responses verbatim. This note is how the Framework
produces that file from a live account. Download records facts; loading
interprets them (wrapper-format.md, principle 3). Download never
transpiles, and load never calls AWS.

## Worked examples

### 1. A classification job

```python
import boto3
from csvpath.macie.macie_downloader import MacieDownloader

session = boto3.Session(profile_name="compliance", region_name="us-east-1")
downloader = MacieDownloader(session=session)
path = downloader.download_job(
    job_id="3ce05dbb7ec5505def334104bf1b3bca",
    path="wrappers/hr-employee-ids.macie.json",
)
```

What it calls, in order, all read-only:

```
sts       GetCallerIdentity                        account id
macie2    DescribeClassificationJob(jobId)         -> aws.classificationJob, selection
macie2    ListManagedDataIdentifiers (all pages)   -> managedDataIdentifiers.available
macie2    GetCustomDataIdentifier(id), each        -> customDataIdentifiers[]
macie2    GetAllowList(id), each                   -> allowLists[].settings
s3        GetObject(bucket, key), each words list  -> allowLists[].contents
macie2    ListFindingsFilters (all pages)
macie2    GetFindingsFilter(id), each              -> findingsFilters[]
```

Then it builds the wrapper, **validates it with `MacieWrapperLoader`
before writing** (a download that produces a wrapper we would refuse to
load is a bug, and fails here), and writes it. Loading is the existing
step:

```python
paths.paths_manager.add_named_paths_from_file(name="hr", file_path=path)
```

### 2. The account's automated-discovery template

```python
path = downloader.download_template(path="wrappers/discovery.macie.json")
```

```
macie2    GetAutomatedDiscoveryConfiguration       sensitivityInspectionTemplateId
macie2    GetSensitivityInspectionTemplate(id)     -> aws.sensitivityInspectionTemplate
... then managed identifiers, custom identifiers, allow lists and filters
    as for a job
```

A template means "the automated-discovery recommended set, plus
includes, minus excludes" (wrapper-format.md), so its selector is
`RECOMMENDED`.

### 3. An allow list the Framework cannot read

The job uses a words list in a bucket our role cannot read:

```
s3:GetObject denied on s3://acme-macie-lists/public-names.txt
```

The download still writes the wrapper, with the list's `contents.status`
`ACCESS_DENIED`, no entries, and a warning:

```json
"warnings": [
  { "code": "ALLOW_LIST_UNREADABLE", "subject": "b8c2d4f6h1j3l5n7p9r0sa",
    "message": "s3:GetObject denied on s3://acme-macie-lists/public-names.txt" }
]
```

Loading reports the list as not translated, and every run's report says
it was missing (as today for a handcrafted wrapper with such a list).
Macie's own status for the list (`status.code`, e.g.
`S3_OBJECT_ACCESS_DENIED`) is a separate fact, kept verbatim, with its
own warning `MACIE_ALLOW_LIST_STATUS` when not `OK`.

### 4. A failure that stops the download

```
MacieException: macie2 DescribeClassificationJob 3ce05...: AccessDeniedException:
User arn:aws:iam::123456789012:user/ci is not authorized to perform macie2:DescribeClassificationJob
```

Anything other than the allow-list reads above stops the download and
writes nothing: a wrapper missing a custom identifier, or with a guessed
managed identifier list, would silently change what is detected.

## How the selection is resolved

The wrapper pins the concrete managed identifier list at download time
(`managedDataIdentifiers.resolved`), since `ALL`, `EXCLUDE` and
`RECOMMENDED` follow AWS's lists as they change.

| Selector | `resolved` |
|---|---|
| `INCLUDE` | the job's `managedDataIdentifierIds` |
| `EXCLUDE` | everything `ListManagedDataIdentifiers` returns, less the job's ids |
| `ALL` | everything `ListManagedDataIdentifiers` returns |
| `NONE` | nothing |
| `RECOMMENDED` (or none given) | the jobs recommended list asset, as of its date |
| template | the automated-discovery recommended list asset, plus includes, less excludes |

**The recommended lists** are published only in the Macie documentation,
not through the API. The Framework ships each as a dated asset:

```
csvpath/macie/rulesbase/recommended/
  jobs.json                 { "source": <AWS page>, "retrieved": "2026-11-08", "ids": [...] }
  automated_discovery.json
```

`resolution.recommended_list` records which, e.g.
`"jobs-recommended@2026-11-08"`. A resolved id that
`ListManagedDataIdentifiers` does not return (AWS retired it since our
asset's date) is dropped with a warning `RECOMMENDED_ID_UNAVAILABLE`, so
the wrapper never claims an identifier AWS no longer runs.

## Permissions

A least-privilege policy for the downloading identity:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow",
      "Action": [
        "macie2:DescribeClassificationJob",
        "macie2:GetAutomatedDiscoveryConfiguration",
        "macie2:GetSensitivityInspectionTemplate",
        "macie2:ListManagedDataIdentifiers",
        "macie2:GetCustomDataIdentifier",
        "macie2:GetAllowList",
        "macie2:ListFindingsFilters",
        "macie2:GetFindingsFilter"
      ],
      "Resource": "*" },
    { "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::<allow-list bucket>/<allow-list key>" }
  ]
}
```

plus `kms:Decrypt` on the key, if an allow-list object is encrypted with
a customer managed KMS key. `sts:GetCallerIdentity` needs no permission.
The docs page will carry this policy.

## Credentials and region

The caller passes a `boto3.Session`, so every credential source boto3
supports works (profiles, SSO, environment, instance roles) and the
Framework holds no secrets. The region is the session's: Macie is
regional, and a job id is only meaningful in its region. A session
without a region is refused.

A later convenience (not in this step): `[macie] aws_profile` and
`aws_region` in `config.ini`, and a FlightPath or CLI command.

## What the download never does

- writes to AWS, starts or changes a job, or enables Macie;
- reads data Macie scans (only the allow-list objects the job names);
- transpiles or loads: that stays a separate, offline step;
- records who downloaded (CloudTrail answers that), only when.

## Open questions

1. **Templates have no ARN.** `GetSensitivityInspectionTemplate` returns
   no ARN (unlike `DescribeClassificationJob`'s `jobArn`), so a
   template-based csvpath has no `macie-source-arn` and its findings'
   `csvpath.source_arn` is null. Proposal: leave it null rather than
   build an ARN AWS does not issue; `macie-template-id` identifies it.
2. **Findings filters are account-wide**, not per job. Proposal: download
   all, as wrapper-format.md says; they are recorded, not applied.
3. **Soft-deleted custom identifiers** a job still uses: kept, with the
   existing `CDI_DELETED_BUT_SELECTED` warning, as Macie keeps using them.
4. **Large words lists.** Macie caps a words list (we believe 100,000
   entries and 35 MB; to confirm from the AWS docs when building).
   Proposal: read it whole, record its sha256, and refuse an object over
   Macie's limit (Macie itself could not use it).
5. **Where the wrapper file goes.** Proposal: the caller's `path`; a
   `.macie.json` suffix required; an existing file is not overwritten
   unless `overwrite=True`, so an earlier download is never lost by
   accident.

## Testing

- **Offline, the default.** botocore's `Stubber` serves canned responses
  and checks every request's parameters and every response against AWS's
  `macie2`, `s3` and `sts` service models, so a misspelled parameter or a
  wrong response shape fails without an AWS account. One test per
  example above, plus pagination (two pages of identifiers and filters),
  each selector, each warning, and each stopping error.
- **The round trip.** Each downloaded test wrapper is loaded and run, so
  download, load and run are tested together.
- **Live, once, with David's OK.** One account, one bucket, 5 to 10 small
  CSV files, one job with a custom identifier, a regex allow list and a
  words list, and the automated-discovery template. Run the downloader,
  load, run, and compare our findings with the job's real Macie findings.
  That is also the first fidelity check (worklist item 8). Cost: under a
  dollar a month (David, 2026-11-08). Not part of the regular suite.

## PR plan

1. The recommended-list assets, with their sources and dates.
2. `MacieDownloader` with the Stubber tests and the round trip.
3. The docs: a "Getting a wrapper" page with the policy, and the
   quickstart's step 1 updated.
4. The live check, when the account is ready.
