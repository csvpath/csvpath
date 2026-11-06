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
4a. **Project rulesbase for the stand-ins.** Copy the packaged catalog into
   the project on load, never overwrite it, resolve a hierarchy (project,
   then Framework, then a `common.json` shared with other rule systems).
   From David's notes; deferred until there is more than one identifier
   to customize (David, 2026-11-01).
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
   - **Group A, health and payments:** UDI (GS1,
     HIBCC, ICCBBA formats with check characters), Canada health number
     (by province; the checks need confirming), EHIC card numbers (EU and
     Finland; the format needs confirming).
   - **Group B, done:** `FormatDetector` and the format notation; UK
     NINO, US and Canada bank account, card security code, pair
     17_group_b_first. Passports (7), pair 18_passports. Phone numbers
     (7), pair 19_phones; national numbers can be several countries'
     (accepted for the first release, David 2026-11-05). Next, in
     `group-b-design.md` order: dates done (birth date, card expiration,
     pair 20_dates); next driver's licenses, then the rest.
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
7. **boto3 download** into a wrapper. Needs an AWS account, region and
   permissions agreed with David first.
8. **One-time fidelity scan against real Macie** (billed; ask first) to
   confirm the interpretations in transpile-design.md: three for custom
   identifiers, nine for managed ones.

## Decide at release planning

- **Alphanumeric CNPJs** (Brazil, issued from July 2026). Needs the
  check-digit rule for letters confirmed from Receita Federal before it
  is built. Until then the converter reports BRAZIL_CNPJ_NUMBER as
  partially translated. Not an MVP blocker for now: Brazil is not a
  target market, and the users most exposed to the gap would be unlikely
  to rely on the MVP for such sensitive use. A gap to close, with a final
  decision when deciding on a first release (David, 2026-11-02).

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
