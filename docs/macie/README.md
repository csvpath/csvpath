# AWS Macie rules in CsvPath

**Status: first draft, November 2026.** For technical review. Details may
change before release.

## What it is

[Amazon Macie](https://aws.amazon.com/macie/) finds sensitive data in S3:
names, card numbers, national ids, credentials and so on. A Macie
classification job is set up with **custom data identifiers** (your
regexes), **managed data identifiers** (AWS's built-in detectors) and
**allow lists**.

The CsvPath Framework reads that setup and runs the same rules against
your tabular data, with no call to AWS when it runs. One Macie job
becomes one csvpath in a named-paths group:

```
 your Macie setup          CsvPath                         your data
 ──────────────────        ─────────────────────────        ──────────
 classification job   ──►  a .macie.json wrapper      ──►   CSV files
 custom identifiers        converted to one csvpath         registered as
 managed identifiers       in a named-paths group           named-files
 allow lists               (CVL you can read and edit)
                           run like any other group:
                           findings, errors, printouts,
                           and a copy of every input
```

## Why

- **The same rules earlier in the pipeline.** Check data at the point it
  arrives or is produced, before it lands in the bucket Macie scans.
- **Outside AWS.** Data that never reaches S3 can still be checked
  against the rules the compliance team owns in Macie.
- **A record you can audit.** A named-paths group run keeps a copy of
  every rule and list it used, with hashes, next to its results (see
  [reproducibility](reproducibility.md)).
- **Readable rules.** The generated csvpath shows each identifier's
  regex, keywords, distance and severity as plain function arguments.

## How it works, in short

1. **A wrapper.** Macie's configuration is spread over several AWS
   resources. The Framework's `.macie.json` wrapper holds all of it in
   one file: the job, its custom identifiers, its resolved managed
   identifiers and its allow lists, with the AWS responses kept verbatim
   (format: `specs/macie/wrapper-format.md`).
2. **Load.** `add_named_paths_from_file()` converts the wrapper to one
   csvpath and loads it as a named-paths group, as it does for ODCS
   contracts. The conversion report says exactly what was and was not
   translated.
3. **Run.** The group runs against a named-file. Every cell of every line
   is checked by every identifier.
4. **Results.** Macie-style findings (`macie_findings`, in the same shape
   as Macie's own findings), one error per detailed occurrence, and a
   readable summary on the `macie` print stream.

## Our approach to fidelity

Custom data identifiers and allow lists are translated directly: their
behavior is documented by AWS and reproduced in the Macie functions.

Managed data identifiers are AWS's own code, which AWS does not publish.
AWS does publish each one's keywords, its severity table, and sometimes
its rules. For each we built a **stand-in**: a detector that follows what
AWS documents and the issuer's published rules (check digits, formats).
**149 managed identifiers have a stand-in.** Each carries a fidelity tier
and is listed in [the managed identifier reference](managed-identifiers.md).

Where a stand-in detects less than Macie says Macie detects, the catalog
marks it **partial** and every conversion that uses it says so. Where we
are unsure, we say so: see [limitations](limitations.md).

**The Macie side fails loudly.** A rule we cannot translate faithfully
stops the conversion, never silently weakens it. A missed card number or
national id can become a legal problem, so a shortfall must be visible.

## Pages

| Page | What it covers |
|---|---|
| [Quickstart](quickstart.md) | Load a wrapper, run it, read the findings |
| [What gets translated](translation.md) | Custom and managed identifiers, allow lists, keywords, severity, the conversion report |
| [Results and findings](results.md) | Printouts, errors, the `macie_findings` document, limits |
| [Reproducibility](reproducibility.md) | Group runs as an auditable record; standalone runs for fast checks |
| [Customizing the stand-ins](customizing.md) | The project rulesbase: tuning keywords, formats and severities |
| [Limitations](limitations.md) | What is not supported yet, and what we want road-test feedback on |
| [Managed identifier reference](managed-identifiers.md) | Every stand-in: category, keyword mode, severity, fidelity |
