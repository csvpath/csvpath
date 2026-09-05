# Normative Examples Coverage Matrix — §6 Functions

Purpose: for each function/rule the compendium (`references_v3_compendium.md`)
asserts, does `normative_reference_examples.txt` actually demonstrate it?
This is a different axis from `function_coverage_matrix.md` (which tracks
function → unit-test coverage against the code registry). This one tracks
compendium requirement → normative example, so we can see where the *spec*
is thin on worked examples, independent of what's built. Hand-maintained;
re-check after either doc changes materially.

Starting with §6 (Functions) per David's request. §3/§4/§5 (Reference
Model, Wildcards, Query vs Resolve) not yet done — next pass.

Legend: **OK** = demonstrated, **THIN** = demonstrated once/narrowly,
**GAP** = zero examples, **N/A** = doesn't apply / covered by the sibling
reference-expressions normative doc instead.

## File accessors (§6.12)

| Function | Status | Note |
|---|---|---|
| `:manifest()` | OK | extensive — global ledger, entity, name_three, all 3 datatypes |
| `:definition()` | OK | files, csvpaths |
| `:data()` | OK | results |
| `:errors()` | OK | extensive, incl. `:idchain()`/`:message()` args |
| `:printouts()` | **GAP** | zero occurrences |
| `:vars()` | OK | |
| `:meta()` | OK | |
| `:unmatched()` | OK | extensive, incl. range restriction |
| `:file()` | OK | results |
| `:log()` | **GAP** | zero occurrences — compendium §6.21 gives 4 examples (3 datatypes + line-count arg), none carried into this file |
| `:readme()` | **GAP** | zero occurrences |

## Ordinal functions (§6.22)

| Function | Status | Note |
|---|---|---|
| `:before()` | **GAP** | zero occurrences anywhere in the file |
| `:after()` | **GAP** | zero occurrences (compendium's own §3.18 CSVPATHS example uses it — `:date(...):after():first()` — never carried into this doc) |
| `:from()` | OK | extensive, both index-mode and date-mode, all 3 datatypes |
| `:to()` | OK | extensive |
| `:index()` | OK | |
| `:last()` | OK | extensive |
| `:first()` | OK | extensive |

## Pure value functions (§6.34)

| Function | Status | Note |
|---|---|---|
| `:year()` | THIN | one occurrence, only as `:name(:year())` |
| `:month()` | **GAP** | |
| `:month_name()` | **GAP** | |
| `:day()` | **GAP** | |
| `:day_name()` | **GAP** | |
| `:hour()` | GAP, self-flagged | doc's own note says "we do not have an :hour(n) as of 13 aug 2026," used only in a `QUESTION:` line — honestly marked, not urgent |
| `:hour_24()` | **GAP** | |
| `:minute()` | **GAP** | |
| `:second()` | **GAP** | |
| `:yesterday()` | OK | 8 occurrences |
| `:today()` | **GAP** | |
| `:date()` | OK | extensive, date-mode ranges |

Six of twelve pure-value functions have zero coverage. Since these are
low-complexity leaf functions this may be low-priority, but it means the
doc gives no worked example of e.g. what `:day_name()` is *for* in a
reference (as opposed to just existing as a value function in the abstract).

## Predicate support functions (§6.36)

| Function | Status | Note |
|---|---|---|
| `:true()` | **GAP** | |
| `:false()` | **GAP** | |
| `:none()` | **GAP** | |
| `:not_none()` | **GAP** | used in the *compendium's* own §5.19/§6.35 examples (`:on_arrival(:not_none())`), never carried into this file |
| `:empty()` | **GAP** | |
| `:not_empty()` | **GAP** | |
| `:regex()` | OK | (as a name_one trailing-token representation) |
| `:having()` | OK | csvpaths, 6 occurrences |

The whole true/false/none/empty family — the functions that make predicate
matching usable with variables — has zero worked examples. Given §6.35's
own illustrative example is `:on_arrival(:not_none())`, this looks like an
oversight rather than a deliberate omission.

## Taxonomy field-accessor families (§6.6–6.8)

| Function | Status | Note |
|---|---|---|
| `:uuid()` | OK | all 3 datatypes, bare/field-accessor form only |
| `:uuid("...")` (argued, pointer form) | **GAP** | §6.44 uses this exact form as its illustrative example of the bare-vs-argued duality; never appears in this file |
| `:run_uuid()` | OK | results |
| `:named_file_uuid()` | **GAP** | listed in §6.7's "uuid" taxonomy group; only appears in the *compendium's* own §6.8 reference-expression example, not here |
| `:named_paths_uuid()` | **GAP** | same |
| `:named_paths_name()` | OK | |
| `:named_results_name()` | OK | |
| `:named_file_name()` | OK | |
| `:fingerprint()` | OK | files, csvpaths — both field-accessor and bare content-hash-search forms |
| `:named_file_fingerprint()` | **GAP** | |
| `:file_fingerprints()` | OK | results, instance scope |
| `:type()` | OK | |

## Function argument roles (§6.37–6.41)

- **Matching-argument on a field accessor** (§6.40's own example: `:error_count(:above(2))`) — **GAP**. Only the bare, unargued `:error_count()` appears in this file; the argued/matching form is never demonstrated. (The `:count(:above(10))` in the file's one `QUESTION:` line is a different, aspirational function, not this pattern.)
- **Nested pointer-as-argument** (`:idchain(...)`, `:message(...)`) — OK, well covered.

## `{...}` string interpolation (§6.42)

**GAP — whole subsection.** Zero occurrences of `{@var}` or `{:function()}` interpolation anywhere in the file, despite §6.42 giving it as the only way to build partner-style dynamic names (`:name("partner-{@company}-orders")`).

## At-most-one-pointer-per-chain (§6.48)

**GAP for the specific illegal case.** The file has several "this combination is rejected" notes (mixing index/date-mode ranges, literal identity + range on the same name_three), but none directly illustrates §6.48's own example — two top-level pointers in one chain (`:last():index(3)`) being illegal while a pointer nested as another function's *argument* doesn't count toward that limit. Worth one explicit pair (legal nested vs. illegal sibling) since it's a subtle, easy-to-get-wrong rule.

## Cross-cutting finding: `:choice()`

Used 1x in the file (`:choice("acme|star|general")`) as if it were a real, committed function — but §3.9c calls it "the mooted `:choice()`" (not yet decided), and it's absent from `function_coverage_matrix.md` (not registered in code). Recommend either marking this example `QUESTION:`/aspirational to match how `:hour()` and `:count()/:above()` are already handled, or — if `:choice()` is actually intended to ship — promoting it out of "mooted" status in the compendium.

## Priority gap list (suggested order to fill in)

1. Predicate family (`:true`/`:false`/`:none`/`:not_none`/`:empty`/`:not_empty`) — zero coverage of an entire, small, well-defined function family.
2. `{...}` string interpolation — zero coverage of a whole compendium subsection.
3. Argued field-accessor matching (`:error_count(:above(2))`-style) — the compendium's own headline example for this concept has no normative counterpart.
4. `:uuid("...")` argued/pointer form — same issue, compendium's own illustrative example missing here.
5. `:before()`/`:after()` — the other half of the ordinal-direction pair (`:from()`/`:to()` are well covered, these aren't at all).
6. `:log()`/`:readme()`/`:printouts()` file accessors — zero coverage each.
7. `:choice()` status resolution (mooted vs. real) — a documentation-consistency fix, not new coverage.
8. Remaining thin pure-value functions (`:month`, `:month_name`, `:day`, `:day_name`, `:hour_24`, `:minute`, `:second`, `:today`) — lower priority, low-complexity leaf functions.

Most of the gap functions above are also absent from `function_coverage_matrix.md`, meaning they're likely not implemented yet either — this is expected, and arguably means these are exactly the places where nailing the normative example *first* will pay off most once implementation resumes.
