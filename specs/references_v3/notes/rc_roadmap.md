# References v3 — Path to RC and Agent Acceptance Testing

A phased, literal checklist from "compendium first pass done" to "v3 is a
feature-complete RC, agent-tested, with a mapped-out FlightPath integration
plan." Each phase has explicit steps and exit criteria. Where a real
judgment call still has to be made rather than just executed, it's flagged
as an open decision, not glossed over. Update this file as phases complete
or plans change — it's a working document, not a one-time snapshot.

Companion documents: `deferred_work_bucket_list.md` (the running gap list
this whole roadmap feeds off of) and `references_v3_compendium.md` (the
controlling spec, directive-requirements-only per David's 2026-08-22 call).

---

## Phase 0 — Prerequisites — CLOSED 2026-08-24

- [x] First compendium pass complete (branch `references_v3_docs_edits`,
  merged PR #259).
- [x] **David's second compendium pass** — done. Compendium now has
  numbered `#### N.M` items throughout (99 as of 2026-08-24), a stable
  citation anchor for every discrete requirement. Not claimed to be
  gap-free ("I'm sure there are gaps... software is never done") — good
  enough to drive Phase 1 from, which is the actual bar, not perfection.
- [x] **Test-conformance mechanism decided**: a separate file,
  `references_v3_compendium_tests.md`, mirroring the compendium's own
  `#### N.M` numbering, each followed by the test(s) that verify it (or an
  explicit "no test yet" marker — gaps stay visible, never silently
  blank). Skeleton/convention created 2026-08-24; populated for real
  during Phase 1, not backfilled all at once now, since Phase 1 is the
  actual verification pass.

**Exit criteria**: compendium is stable enough to review against; a place
to record test-conformance mappings exists. Both true as of 2026-08-24.

---

## Phase 1 — Block-by-block compendium review — FIRST PASS COMPLETE 2026-08-25

The same process this whole conversation has been doing manually, run
systematically over the entire document instead of piecemeal.

**Status**: all six numbered sections of the compendium (as of David's
own second-pass edits, itself completed alongside this review) have been
checked block by block and recorded in
`specs/references_v3/spec/references_v3_compendium_tests.md`. Real
findings from this pass (function-family audits, the `:home()` scoping
decision, the `paths`-vs-`values` compatibility matrix, several stale/
wrong text passages, two numbering slips) are on the bucket list or
already fixed in the compendium directly. Not claimed to be the last
pass ever needed — David continues to edit the compendium, and each
future edit should get the same block-level scrutiny, not just new
material added since the last review.

**Per block, do this:**
1. Read the block as a standalone claim (or small group of claims).
2. Verify every factual/behavioral claim against current code —
   **live-test where feasible, don't reason from memory of prior
   sessions or from reading code alone.** This session's own experience:
   several claims that looked obviously fine on inspection turned out
   wrong or half-wrong under an actual live test (the `:manifest():last()`
   symmetry gap, the FILES `orders`-vs-`orders.csv` bug, the `'*'`+`:home()`/
   `:definition()` four-way failure, the Rule 2/3 example failures).
3. Classify the outcome:
   - **Accurate, already tested** — no action, move on.
   - **Accurate, not yet tested** — add to the "tests needed" list (below).
   - **Text is stale/wrong relative to current code** — fix the text.
   - **Code doesn't yet match correct spec intent** — add/update a
     bucket-list item.
   - **Genuinely ambiguous / needs a decision** — surface it as a question,
     get David's call, then route to one of the two lines above.
4. Log the outcome before moving to the next block — don't rely on
   memory across a long pass; write it down (bucket list, tests-needed
   list, or a text correction) as you go.

**Tests-needed list — resolved, no separate file needed.** In practice,
`references_v3_compendium_tests.md`'s own `*(no test yet)*` markers
turned out to serve exactly this purpose, item by item, with more
precision than a separate flat list would have (each gap is already tied
to the specific requirement it's missing a test for, and to whichever
bucket-list item tracks the underlying build work). No separate file was
needed.

**Exit criteria — met for the first pass**: every section of the
compendium has been checked; every real gap found is on the bucket list;
every compendium item has an entry in the test-conformance map, whether
a real test citation or an explicit "no test yet."

---

## Phase 2 — Close the gaps

1. Work the bucket list. Suggested order, not a hard rule: mechanical/
   obvious fixes and the tests-needed list first (per David's own
   preference), then items needing a design decision, in whatever order
   makes sense once you're looking at the actual list at the time.
2. For any item that needs a decision before it can be built (several
   already flagged this way — e.g. `:home()` retirement naming, the
   `SELECTOR_WHEN_ARGUED` mechanism shape, the `resolve_kind` dispatch
   fix), get David's call *before* implementing, not after.
3. Implement, write/update tests, remove the item from the bucket list.
4. Run the full suite periodically as items land (per existing project
   practice — full local-backend run is ~2 minutes, run it often, not
   just at the end).

**Exit criteria**: bucket list is empty, or every remaining item is
*explicitly* marked "deferred past RC, not blocking" with David's
sign-off recorded — never silently dropped.

---

## Phase 3 — Full internal consistency pass

1. Re-read the entire compendium fresh, end to end, after Phase 2's
   changes have landed — confirm every claim still matches the code (some
   will have changed *because of* Phase 2's own fixes).
2. Confirm every claim has a real, passing, identifiable test, using
   whichever test-conformance mechanism Phase 0 settled on.
3. Confirm the bucket list is genuinely empty (or every remaining item is
   a signed-off deferral, per Phase 2's exit criteria).
4. Full suite run, clean, same known non-v3 baseline failures as always
   (SFTP/S3/Nos, per existing project knowledge) and nothing new.

**Exit criteria**: spec, code, and tests all agree with each other;
nothing outstanding on the bucket list without an explicit deferral.

---

## Phase 4 — RC decision

1. Review test coverage holistically, not just "does every compendium
   claim have a test" — edge cases, error paths, and cross-datatype
   consistency (FILES/CSVPATHS/RESULTS behaving the same way for the same
   concept, per the project's own established preference).
2. David and I jointly decide: is this a feature-complete RC?
   - **Not yet** — name the specific gaps, loop back to Phase 2/3 for
     just those, re-attempt Phase 4.
   - **Yes** — record the decision (a dated note in the compendium or
     this file is enough, no need for elaborate versioning machinery),
     proceed to Phase 5.

**Exit criteria**: an explicit, dated "this is RC" decision, not an
implicit drift into the next phase.

---

## Phase 5 — Agent-facing REPL harness

**This phase needs its own short design pass before building** — treat it
as a real mini-project, not a one-line task. Open questions worth settling
first (not answered here; answer when this phase actually starts):

- **Interface**: an interactive CLI REPL, a thin Python API with a
  scripted loop, or both? David wants to use it directly, not just
  agents, so it needs to be genuinely pleasant to drive by hand, not
  only scriptable.
- **Data**: does it run against a real, populated archive (named-files/
  named-paths/named-results actually registered somewhere), synthetic
  fixtures generated on demand, or a "seed a scratch archive, then query
  it" mode? Probably needs at least the seeding mode, given fuzzing wants
  reproducible, disposable state.
- **Capabilities**: parse a reference string; run `query()`/`resolve()`/
  `resolve_from()`; display results in an inspectable form (not just raw
  reprs); run `ReferenceExpression3` combinations; support both
  interactive single queries and scripted/batch fuzzing runs.
- **Fuzzing shape**: generate/mutate reference strings against the real
  grammar (not just hand-written adversarial cases) to find crashes,
  silent-wrong-answers, or spec/code mismatches the compendium review
  didn't catch.

**Steps:**
1. Write a short design note answering the questions above — get
   David's sign-off before building (this is a natural point to use plan
   mode properly, once we're actually here).
2. Build a minimal version; try it against a handful of real scenarios
   from the normative examples file.
3. Iterate based on David's own hands-on use, not just agent use.

**Exit criteria**: David can write and execute a reference interactively
end to end; an agent can be pointed at the harness and use it to explore/
validate/fuzz v3 without hand-holding.

---

## Phase 6 — Agent acceptance testing

1. Use the harness to run broad, adversarial exploration against the
   compendium's stated requirements — malformed references, edge-case
   argument combinations, cross-datatype `ReferenceExpression3` cases,
   deliberately weird but grammatically legal traversal shapes.
2. Triage anything found the same way as Phase 2 (bucket-list it, or fix
   immediately — David's call each time, not an automatic "fix and move
   on").
3. Repeat until at least one full adversarial pass runs clean with
   nothing new surfacing.

**Exit criteria**: David is satisfied v3 has been genuinely exercised by
an independent (agent) actor working from the spec, not just validated
by the test suite the same people who wrote the code also wrote.

---

## Phase 7 — FlightPath integration planning

Explicitly a **planning** phase, not execution — produces its own,
separate roadmap doc, doesn't try to build the integration here. v2 stays
CsvPath Framework's own operational infrastructure throughout; v3 is being
enabled for FlightPath first, not replacing v2 yet.

1. Identify which FlightPath features/flows would actually consume v3
   references (needs David's own FlightPath domain knowledge — not
   visible from this codebase alone).
2. Define the integration boundary/API surface v3 needs to expose for
   those flows specifically, not a generic "expose everything" surface.
3. Decide the rollout shape (feature-flagged, parallel-running, staged
   by FlightPath feature, etc.).
4. Write a dedicated FlightPath-integration plan document once the above
   is scoped — this roadmap's job ends at the handoff to that plan.

**Exit criteria**: a scoped, written FlightPath integration plan exists,
separate from this document.
