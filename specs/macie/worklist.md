# Macie worklist

Open work in two kinds (David, 2026-11-16):

- **Completeness**: what Macie does that we do not do yet, or do
  differently. This is the road to fidelity.
- **Extensions**: what goes beyond Macie.

Then what to settle before a first release, and a record of what is
done. Add an item the moment something is deferred.

## Completeness: closing the gaps with Macie

### Identifiers

- **Partial stand-ins**, each marked in the catalog and reported by every
  conversion that uses it:
  - Brazil CNPJ: no alphanumeric CNPJs (issued from July 2026); see
    release planning below.
  - Australia TFN: no 8 digit TFNs.
  - UK tax identification: UTRs only, no TRNs.
  - US HICN: SSN-based only, no Railroad Retirement Board numbers.
  - Canada health number: British Columbia, Ontario and Quebec only;
    other provinces publish no check.
  - Germany identity card: not confirmed against Macie, which reported
    none of seven forms (live probes, 2026-11-14).
- **Checks not confirmed from an authoritative source**: Italy's BBAN CIN
  letter (not checked), the EHIC as 80 and a country code (and the card's personal ID, not
  detected). Add each check when a source confirms it.
- **NAME and ADDRESS** (Macie's machine learning identifiers): checked by
  Jev from the columns' masked shapes when `[macie] review` names them,
  in a separate `jev` section (2026-11-19). Names inside free text are
  missed; ask road-testers how often that matters.

### Fidelity

- **The open fidelity items** in `transpile-design.md` (1 to 26, less
  those settled by the live check and probes). Road-testers settle some;
  a probe settles one for cents.
- **Phones for countries other than the US**: after the fourth and
  fifth probes (2026-11-16, -17), an international number is found only
  unbroken (`international_unbroken_only` in the catalog, 2026-11-17).
  Left, not explained by format: Macie reports no Italian number in any
  form, and no German, Italian or Spanish national number after a
  keyword (`limitations.md`).
- **A keyword written against a value** (`SSN123-45-6789`): not a word
  for us; not seen for Macie.

### The download

- ~~**`template=True` is not checked live**~~ Done (2026-11-16): David
  enabled automated discovery; the download, the load and a run work
  live (35 identifiers, the post-2023 set; `live-check-2026-11-11.md`).
  The static set of 100 can only be checked with stubs.

### Real-world files

- ~~**Header handling (#479).**~~ Done (2026-11-18). Measured: leading
  blank lines and header-only files are handled; a headerless or
  title-line file loses its header keywords, as Macie does (sixth probe,
  8 of 8 rows agree). A first line holding a value is read as data: no
  column names (Macie's are null), no header keywords, and a loud
  warning, so a value never becomes a column name. `skip()` leaking into
  the next line (#478) fixed (#737). Left: Macie also gives a title line
  no column names, by a rule we do not know (road-testers); a way to say
  where the header is would go beyond Macie (extension).
- **Directory loads under a name** refuse Macie wrappers, as they refuse
  ODCS contracts. Appending with `add_named_paths_from_file(append=True)`
  works for both.
- **Per-identifier detail caps from the rulesbase** are not wired yet
  (`macie_cdi`'s optional 8th argument exists; the converter does not
  write it).

### Design questions to revisit

- **Should findings ever make a run invalid?** A Macie csvpath stays
  `is_valid` even with HIGH findings, so a group can look valid while it
  holds sensitive data.
- **A csvpath after a Macie csvpath with `source-mode: preceding`** gets
  only the lines with findings. That could be a feature (e.g. redaction)
  or a surprise. Collecting the clean lines instead works today with
  `return-mode: no-matches` (tried 2026-11-18); a build would add a
  config key, a loud breaker and a printout: `clean-lines-design.md`.
- **Limits are fixed when the group is loaded**: changing `[macie]` in
  config.ini takes effect when the group is reloaded. David is not
  worried about this for now (2026-10-31).

## Ask road-testers about

Known false positive and false negative risks, to ask people road-testing
the stand-ins for specific feedback on (David, 2026-11-06). Each is also a
fidelity item in transpile-design.md.

- **Keywords are whole words** (fidelity item 3, settled 2026-11-15).
  The old risk, short keywords inside longer words, is gone. The new
  one: a keyword written directly against a value (`SSN123-45-6789`) is
  not a word, and we have not seen what Macie does there.
- **Phones outside the US.** An international number counts only
  unbroken; national numbers need a keyword. Macie reported no Italian
  number at all in the probes, and no German, Italian or Spanish
  national number after a keyword. Ask testers with numbers from those
  countries what Macie finds.
- **One value, several countries.** National phone numbers (item 19),
  driver's licenses near English keywords (item 21), Swedish numbers,
  which fit Finland's shape too and share its Swedish keywords, and digit
  runs shared by the Argentina DNI, Colombia cedula and Canada PR number
  can be reported for more than one identifier.
- **Keywords kept as Macie publishes them.** Macie's Greek driver's
  license keyword lacks its first letter (`δεια οδήγησης`), so a number
  after `άδεια οδήγησης` is missed unless `adeia odigisis` is there too;
  Sweden's list has `dlno# ajokortti` as one keyword. Ask testers with
  Greek or Swedish data what Macie finds.
- **Formats that are ours.** Brazil RG takes only Sao Paulo's shape, so
  other states' RGs are missed; the Canada PR number is the UCI only, not
  the card's document number.
- **Provinces left out.** Canada health numbers are detected only for
  British Columbia, Ontario and Quebec (item 24); other provinces' numbers
  have no published check and are missed.
- **EHIC: the card number only** (item 25). We read it as 20 digits, 80
  and a country code, which no official source confirmed; the personal ID
  on the card is not detected. Ask testers with real cards whether
  theirs are found.
- **UDI: written forms only.** GS1 UDIs without their parentheses are
  missed. ISBT 128 UDIs are found in their human readable form, `=/`
  and the Device Identifier; with no check character in the UDI, the
  format is all there is (fidelity B). Ask testers with tissue or blood
  product data whether theirs are found.
- **German ID: no form reported by Macie** (live probes, 2026-11-14).
  We report 2010-format and older numbers with valid check digits; Macie
  reported none of seven. Marked partial in the catalog. Ask testers
  with German data whether Macie reports any, and in what form. (The
  phone and Codice Fiscale differences seen with it were fixed on
  2026-11-15.)
- **Title lines before the header.** Macie gave the columns of a file with
  a title line no names; we name them from the title. Ask testers whose
  exports start with a title what Macie reports.
- **The Jev review sends words without digits as written**, names
  included (decision 3, 2026-11-15). Ask testers whether they need names
  masked too.

## Extensions: beyond Macie

- **The Jev review, next steps** (built: #667, #668, #670; run live,
  #672):
  - a sharper "why" for a keyword in the cell: `MacieReview.why()` reads
    only the header, so it says "a keyword is near the value in the cell,
    or the value needs none";
  - `review_mask_words`, masking capitalised words too, if road-testers
    ask (decision 3);
  - `review = all`, left out of the first build on purpose (decision 4);
  - NAME and ADDRESS: built (2026-11-19), column level, from
    `jev-names-addresses-design.md` and the experiment. Next, if
    road-testers ask: names in free text (option B, sending cell words,
    an explicit opt-in).
- **CVL `jev()` uses `jev-latest`**, which moves; a config key to pin the
  model would make CVL results comparable over time (core, not Macie).
- **Rulesbase `common.json`**, deferred in `rulesbase-design.md`.
- **Italy's 11 digit organization codes** (partita IVA) are detected
  beyond what Macie documents (pair 11); keep, and say so in the docs.
- **Versioning for named-paths groups**, as named-files have (David,
  2026-11-16). The idea was that people version their csvpaths in git;
  that has not held up well. Future work, not Macie-specific.
- **A plain csvpath reload over a Macie group** keeps the Macie catalog
  and lists in `assets/`. Unread, since there is no Macie run without
  Macie functions; remove them if it ever matters.

## Before a first release

- **Docs for bTrade**: `docs/macie/` (10 pages, including `aws.md` and
  `review.md`) is the first draft; more as the partner review asks.
- **Alphanumeric CNPJs** (Brazil, issued from July 2026). Needs the
  check-digit rule for letters confirmed from Receita Federal before it
  is built. Until then the converter reports BRAZIL_CNPJ_NUMBER as
  partially translated. Not an MVP blocker for now: Brazil is not a
  target market, and the users most exposed to the gap would be unlikely
  to rely on the MVP for such sensitive use. A gap to close, with a final
  decision when deciding on a first release (David, 2026-11-02).
- **The SFTP tests**: deselected since the server went down
  (2026-11-03); they need one run against everything since #502.

## Done

A record, oldest first. Details are in the PRs and the specs named.

- **The translation:** `MacieConverter`, wrapper to CVL (pair 01). Loading
  `.macie.json` into named-paths groups, with the wrapper and its report
  copied into the group home; Macie csvpath ids unique in a group (David,
  2026-10-31). The breaker, pair 03 (needed the `stop()` fix, #483/#484).
- **Text allow lists:** `macie_allow_words` via `load_list()` (#499,
  #502), stored in the group's assets; a conflicting list on append is
  refused (pair 09).
- **Managed identifiers, group A** (a check or a fixed structure): credit
  cards (pair 02); US SSN and NPI (04); IBANs, 52 countries (05); Canada
  SIN, UK NHS, VIN (06); Brazil CPF and CNPJ, Chile RUT, Argentina SUBE
  (07); BBANs for France, Germany, Italy, Spain and the UK (08); Spain DNI
  and NIE, India Aadhaar (10); France NIR, Mexico CURP, Italy Codice
  Fiscale and organization codes (11); Germany IdNr, Argentina CUIT and
  CUIL, Australia TFN, UK UTR (12); Spain NIF and CIF, Mexico RFC,
  Colombia NIT, France TIN (13; splits agreed 2026-11-03); all nine
  credentials (14); US DEA, Medicare MBI, ITIN, HICN, NDC, HCPCS (15);
  Germany identity card, France health insurance number, magnetic
  stripe (16); Canada health number (24); EHIC and UDIs, GS1 and HIBCC
  (25), ISBT 128 (2026-11-16, #718); Spain social security number (26).
  Group A is complete.
- **Managed identifiers, group B** (format and keyword): `FormatDetector`
  and its notation; UK NINO, US and Canada bank accounts, card security
  code (17); passports (18); phones (19; several countries' national
  numbers accepted for the first release, David 2026-11-05); dates (20);
  driver's licenses, 17 jurisdictions (21) and the other 15 countries
  (2026-11-18); Argentina DNI, Brazil RG and
  CEP, Colombia cedula, Canada PR, India PAN, UK electoral roll (22); GPS
  and cookies (23). Group B is complete.
- **Project rulesbase:** `specs/macie/rulesbase-design.md` (2026-11-07);
  the overrides merge (#549), load and snapshot (#550), run dir copies
  and the standalone line (#552). User docs, first draft:
  `docs/macie/`, with the managed identifier reference generated from the
  catalog.
- **The download:** `specs/macie/download-design.md`; the recommended sets
  (#560), `MacieDownloader`, `add_named_paths_from_macie()` and
  `docs/macie/aws.md`. Live check 2026-11-11: the docs policy is enough
  (`specs/macie/live-check-2026-11-11.md`).
- **Fidelity against real Macie:** the live check (34 of 43 comparisons
  exact; one cell per location, fixed) and three probes (2026-11-14 and
  -15, same report): keywords match as whole words; a phone with a
  country code and no keyword counts only unbroken or parenthesized;
  the German ID marked partial.
- **The Jev review:** design (`jev-review-design.md`), two experiments
  (`jev-experiment-2026-11-15.md`: `choice()` with our column facts, 29
  of 30 right), the build (`jev-review-build.md`; #667 masks and column
  facts, #668 `JevReviewer`, #670 wiring and `docs/macie/review.md`), a
  live run (#672) and a fake client for the CVL `jev()` tests (#673).
  Decisions settled as proposed (David, 2026-11-15). This replaces the
  earlier idea of Jev as a double check on warnings (2026-11-08).
- **Clean-ups:** a reload without append removes earlier source copies,
  their reports, and the lists only they brought; lists stored with
  `store_list()` are kept (#719, 2026-11-16).
  NAME and ADDRESS are reported as not translated, not dropped.
