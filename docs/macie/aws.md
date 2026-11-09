# Getting the rules from AWS

The Framework reads a Macie classification job's whole setup from your
AWS account and loads it as a named-paths group in one step:

```python
import boto3
from csvpath import CsvPaths

paths = CsvPaths()
session = boto3.Session(profile_name="compliance", region_name="us-east-1")

paths.paths_manager.add_named_paths_from_macie(
    name="hr_ids",
    session=session,
    job_id="3ce05dbb7ec5505def334104bf1b3bca",
)
```

For the account's automated sensitive data discovery settings (its
sensitivity inspection template), use `template=True` instead of a
`job_id`.

From there the group runs as any other: see the
[quickstart](quickstart.md).

## What it reads

Only reads; it never changes anything in AWS, starts a job, or enables
Macie.

| Call | For |
|---|---|
| `sts:GetCallerIdentity` | the account id |
| `macie2:DescribeClassificationJob` | the job: its identifiers, allow lists and selector |
| `macie2:GetAutomatedDiscoveryConfiguration`, `GetSensitivityInspectionTemplate` | a template, instead of a job |
| `macie2:ListManagedDataIdentifiers` | the managed identifiers the account offers |
| `macie2:GetCustomDataIdentifier` | each custom identifier |
| `macie2:GetAllowList` | each allow list |
| `s3:GetObject` | each text allow list's words file |
| `macie2:ListFindingsFilters`, `GetFindingsFilter` | findings filters, recorded but not applied |

## Permissions

A least-privilege policy for the identity the session uses:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
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
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::<allow-list bucket>/<allow-list key>"
    }
  ]
}
```

Add `kms:Decrypt` on the key if a text allow list is encrypted with a
customer managed KMS key. `sts:GetCallerIdentity` needs no permission.

## Credentials and region

You pass a `boto3.Session`, so every way boto3 finds credentials works
(profiles, SSO, environment variables, instance roles), and the Framework
holds no secrets. The session must have a region: Macie is regional, and
a job id belongs to its region.

## Where the rules go

**Nowhere but the named-paths group.** The download is built and checked
in memory, then loaded. The group home holds it as
`<job name>.macie.json`, with its conversion report beside it, and each
group run copies it into the run's `_extra_data/macie/` (see
[reproducibility](reproducibility.md)). No other file is written: a
wrapper holds your text allow lists' entries, which may be real names or
numbers.

The group's manifest records where the rules came from, for example:

```
"source_path": "aws:macie2:us-east-1:123456789012:classification-job/3ce05dbb7ec5505def334104bf1b3bca"
```

(Not an ARN: an automated discovery template has no ARN, and none is
made up.)

To look at what would be loaded first, without loading it:

```python
from csvpath.macie.macie_downloader import MacieDownloader

wrapper = MacieDownloader(session=session).download_job(job_id="3ce05...")
```

`wrapper` is a dict; nothing is written.

## "Recommended" identifiers

A job can use Macie's *recommended* managed identifiers, and a template
always starts from Macie's automated discovery defaults. AWS publishes
those sets only in its documentation, not through the API, so the
Framework ships them as dated copies, and the wrapper records which one it
used (for example `jobs-recommended@2026-11-08`). Accounts that first
enabled automated discovery before 2023-08-02 use Macie's older, static
set; the download reads the account's date and picks the right one.

If a recommended identifier is not among those the account offers, it is
left out with a warning, so a wrapper never lists an identifier AWS does
not run.

## When something goes wrong

- **A text allow list cannot be read** (no `s3:GetObject`, a missing
  object, an empty or over-size list): the download goes on, records the
  problem in the wrapper with a warning, and the list is reported as not
  translated. Its identifiers still run, without it.
- **Anything else** (a missing permission, an unknown job, a custom
  identifier that cannot be read): the download stops and nothing is
  loaded. A wrapper missing part of the job would detect less than the job
  does, without saying so.
- **A deleted custom identifier** that the job still uses is kept, with a
  warning saying it was deleted in Macie, as Macie keeps using it. That is
  distinct from one that cannot be read, which stops the download.
