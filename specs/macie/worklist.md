# Macie worklist

Ordered roughly by when we expect to do it. Blockers first; clean-ups
last. Add an item the moment something is deferred.

## Next

1. ~~**Transpiler: wrapper -> CVL.**~~ Done: `MacieConverter`. Pair 1 is
   reproduced exactly. Not in it yet: per-identifier detail caps from the
   rulesbase (`macie_cdi`'s optional 8th argument).
2. ~~**Loading `.macie.json` into named-paths groups.**~~ Done:
   `add_named_paths_from_file` and `add_named_paths_from_dir` load
   wrappers like ODCS contracts. The wrapper is copied into the group home
   with `<file>.report.json` beside it. A Macie csvpath's id must be
   unique in its group (David, 2026-10-31).
3. ~~**Pair 03_breaker.**~~ Done. It needed the `stop()` fix (#483, PR
   #484) so the line that trips the breaker is matched.

## Design questions to revisit

- **Should findings ever make a run invalid?** A Macie csvpath stays
  `is_valid` even with HIGH findings, so a group can look valid while it
  holds sensitive data.
- **A csvpath after a Macie csvpath with `source-mode: preceding`** gets
  only the lines with findings. That could be a feature (e.g. redaction)
  or a surprise.
- **Limits are fixed when the group is loaded**: changing `[macie]` in config.ini
  takes effect when the group is reloaded. David is not worried about this
  for now (2026-10-31).

## After that

4. ~~**Managed identifiers, group A, first batch: credit cards.**~~ Done:
   `macie_mdi`, the packaged catalog, `CreditCardDetector`, Luhn, and pair
   02_credit_card. Second batch done: US SSN and NPI, pair 04_us_ids.
   Third batch done: IBANs, all 52 countries, pair 05_iban. Fourth batch
   done: Canada SIN, UK NHS, VIN, pair 06_sin_nhs_vin. Fifth batch done:
   Brazil CPF and CNPJ, Chile RUT, Argentina SUBE, pair 07_latam. Sixth
   batch done: Spain DNI and NIE, India Aadhaar, pair 10_es_in. Seventh
   batch done: France NIR (INSEE), Mexico CURP, Italy Codice Fiscale
   (people's 16 character codes and organizations' 11 digit codes), pair
   11_fr_mx_it. Eighth batch done: Germany IdNr, Argentina CUIT and CUIL
   (individuals and organizations), Australia TFN (partial: no 8 digit
   TFNs), UK UTR (partial: no TRNs), pair 12_tax_ids. Ninth batch done:
   Spain NIF and CIF, Mexico RFC and Colombia NIT (each for individuals
   and organizations), France TIN, pair 13_tax_ids_2; the splits agreed
   with David on 2026-11-03. Credentials done: all nine of Macie's
   credential identifiers, pair 14_credentials. Group A left: the
   Germany national id card, the US DEA number, US ITIN, Medicare MBI.
   Then group B (David, 2026-11-03: either order, as long as both get
   done).
4b. ~~**BBANs for France, Germany, Italy, Spain and the UK**~~ Done: the
   bank detector, pair 08_bban. The five identifiers are no longer
   partially translated. Italy's CIN letter is not checked (rule not
   confirmed from an authoritative source); if it is confirmed, add it.
4a. **Project rulesbase for the stand-ins.** Design agreed 2026-11-07:
   `specs/macie/rulesbase-design.md` (an overrides file merged over the
   packaged catalog; the merged catalog snapshotted into the group; group
   runs copy their Macie inputs into `_extra_data/macie/`; `common.json`
   deferred). PR 1 (merge, #549), PR 2 (load and snapshot, #550) and PR 3
   (run dir copies, the standalone line, #552) built. User docs, first
   draft for partner review: `docs/macie/` (8 pages; the managed
   identifier reference is generated from the catalog and checked by
   `tests/macie/test_macie_docs.py`).
5. ~~**Text allow lists**~~ Done: `macie_allow_words` via `load_list()`
   (#499) and `configure_named_paths()` (#502); lists stored in the group's
   assets on load; a conflicting list on append is refused. Pair
   09_text_allow_list.
6. **Managed identifiers still to build** (inventory from Macie's PII,
   PHI, financial and credentials pages, 2026-11-04). Group A has a check
   or a fixed structure; group B is format plus keyword; group C needs
   ML or a gazetteer.
   - **Done:** US DEA, Medicare MBI, US ITIN, HICN (partial), NDC,
     HCPCS, pair 15_us_health.
   - **Done:** Germany identity card, France health insurance number,
     card magnetic stripe, pair 16_group_a_more.
   - **Done:** Canada health number (British Columbia, Ontario, Quebec;
     pair 24_ca_health). EHIC card numbers (EU and Finland) and medical
     device UDIs (GS1 and HIBCC), pair 25_ehic_udi. Group A is complete
     apart from ISBT 128 UDIs.
   - **Group B, done:** `FormatDetector` and the format notation; UK
     NINO, US and Canada bank account, card security code, pair
     17_group_b_first. Passports (7), pair 18_passports. Phone numbers
     (7), pair 19_phones; national numbers can be several countries'
     (accepted for the first release, David 2026-11-05). Next, in
     `group-b-design.md` order: dates done (birth date, card expiration,
     pair 20_dates); driver's licenses done for 17 jurisdictions (pair
     21_drivers_licenses). The rest of group B's shapes done (Argentina
     DNI, Brazil RG and CEP, Colombia cedula, Canada permanent resident,
     India PAN, UK electoral roll, pair 22_group_b_rest). GPS
     coordinates and HTTP cookies done (`LatLongDetector`,
     `CookieDetector`, pair 23_gps_cookie). Group B is complete apart
     from the driver's license backlog below.
   - **Backlog, driver's licenses** (David, 2026-11-06): Finland, Greece,
     Hungary, Ireland, Latvia, Lithuania, Luxembourg, Malta, Netherlands,
     Poland, Portugal, Romania, Slovakia, Slovenia, Sweden. Microsoft
     Purview's per-country pages have the patterns (about 4k tokens each
     to fetch).
   - **Group B:** driver's licenses (32 identifiers; the US one covers
     50+ state formats), passports (7), phone numbers (7), UK NINO, UK
     electoral roll, Canada permanent resident card, India PAN, Brazil RG,
     Argentina DNI, Colombia cedula, US and Canada bank account numbers
     (9-17 digits, no spaces), credit card expiration and security code,
     birth dates, GPS coordinates, HTTP cookies, Brazil CEP codes.
   - **Group C, report as not supported:** NAME and ADDRESS.
   Order (David, 2026-11-04: either order is fine as long as both get
   done): finish group A first, as it reuses the existing detectors,
   then group B after a design pass with David on a generic pattern
   detector.
6b. ~~**`SPAIN_SOCIAL_SECURITY_NUMBER`**~~ Done: missed by the item 6
   inventory, found 2026-11-08 when building the recommended-list assets
   (it is in every recommended set). Format only, fidelity B: the NAF's
   control digits are not checked, as no authoritative rule was found.
   Pair 26_es_ssn.
7. **boto3 download** into a wrapper. Design draft:
   `specs/macie/download-design.md` (2026-11-08). Offline first with
   botocore's Stubber; one live check in David's account later (one
   bucket, 5 to 10 small files, under a dollar a month). Built: the
   recommended sets (#560), `MacieDownloader`, and
   `add_named_paths_from_macie()` with `docs/macie/aws.md`. Left: the
   live check.
8. **One-time fidelity scan against real Macie** (billed; ask first) to
   confirm the interpretations in transpile-design.md: three for custom
   identifiers, nine for managed ones.

## Ask road-testers about

Known false positive and false negative risks, to ask people road-testing
the stand-ins for specific feedback on (David, 2026-11-06). Each is also a
fidelity item in transpile-design.md.

- **Short keywords match inside words** (fidelity item 3). Brazil's `rg`
  matches `org`, `large`, a `cargo` header; `cep` matches `receptor`,
  `exception`; also `mc`, `pan`, `card` and France's `social`. A number
  of the right shape next to such a word is reported.
- **Keywords need their accents** (item 22). `cedula de ciudadania`
  without accents is not Colombia's keyword, so a cedula labeled that way
  is missed. Brazil's CEP list has both forms only because Macie lists
  both.
- **One value, several countries.** National phone numbers (item 19),
  driver's licenses near English keywords (item 21) and digit runs
  shared by the Argentina DNI, Colombia cedula and Canada PR number can
  be reported for more than one identifier.
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
- **Spain SSN: format only.** The control digits of a NAF are not
  checked (item 26), so any 12 digits of the right layout near a keyword
  count. Ask testers with Spanish payroll data for false positives.
- **UDI: GS1 and HIBCC only.** ISBT 128 (blood and tissue products) is
  missed, as are GS1 UDIs written without their parentheses. The
  keywords `med` and `blood` match inside many words.

## Decide at release planning

- **Alphanumeric CNPJs** (Brazil, issued from July 2026). Needs the
  check-digit rule for letters confirmed from Receita Federal before it
  is built. Until then the converter reports BRAZIL_CNPJ_NUMBER as
  partially translated. Not an MVP blocker for now: Brazil is not a
  target market, and the users most exposed to the gap would be unlikely
  to rely on the MVP for such sensitive use. A gap to close, with a final
  decision when deciding on a first release (David, 2026-11-02).

## After the MVP release

- **Jev as a double check on warnings** (David, 2026-11-08). David is
  adding Jev functions to CVL first (issue #558) to get a feel for it;
  if it works as hoped, consider how Macie could use it.

## Clean-ups (not blockers)

- **Stale source copies in group homes (Macie and ODCS).** Reloading a
  group without append rewrites `group.csvpaths` but leaves the wrapper and
  contract copies, and their `.report.json` files, from earlier loads. The
  group home can then describe rules it no longer runs. Cleanup should be
  automatic (David, 2026-10-31). Text allow lists in `assets/` are the
  same: a reload without append replaces the lists the new wrapper has,
  and leaves the others.
- **Directory loads under a name** refuse Macie wrappers, as they refuse
  ODCS contracts. Appending with `add_named_paths_from_file(append=True)`
  works for both.

- **Header handling (#479).** The generated scan `$[1*]` assumes the
  header is line 0. Headerless files, leading blank lines, prolegomena
  lines and header-only files need a graceful answer. Related bug:
  `skip()` in the last expression skips the next line (#478).
- **Group C managed identifiers** (NAME, ADDRESS): unsupported. Report
  them as not translated rather than silently dropping them.
