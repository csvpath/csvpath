
# REFERENCE EXPRESSIONS

A reference expression is a logical operation(s) on references. The goal is to answer questions that a single reference is insufficient to answer on its own. For example:

    *"find all the named-files that were used in runs where the named-paths group was updated yesterday."*

We can find all the named-files used in runs from the RESULTS datatype. And we can find all the named-paths group updated yesterday from the CSVPATHS datatype. But we need a set operation-like evolution applied to both to answer the full question. The set operation and its references is a reference expression.

The result of a reference expression is ReferenceResults, same as the result of a single reference.


## OPERATIONS

A reference expression has one operation which is one of:
- UNION
- SUBTRACT
- INTERSECT

They do exactly as you would think. UNION bags the two ReferenceResults sets together. SUBTRACT removes the right-hand side from the left-hand side (as in "ref subtract ref"). And INTERSECT returns bag of the ReferenceResults items found on both sides.

At this time we don't contemplate ordering results, though SUBTRACT will retain the order of the left-hand side.


## SUB-REFERENCE EXPRESSIONS

A reference expression may have another reference expression on either side. Each side is reduced to a ReferenceResult before the set operation is applied.


## EXAMPLES

The code below is for illustration only. It is both not settled in form and very likely not fully interpretable as Python. Treat it as speculative pseudocode to help plan the Reference Expressions API.

#
# find the named-paths groups versions that caused errors yesterday
#
exp = ReferenceExpression.intersect()
#
# $*.csvpaths.:flatten():from(:yesterday()).:identity(@identities)):has_errors():named_paths_uuid()
#
fails = exp.results_reference("*")
ids = ["my_validations", "new_validations"]
fails.set("identities", ids).
fails.name_one = "flatten():from(:yesterday())")
fails.name_three = ":identity(@identities):has_errors()")
#
# $*.csvpaths.:all():having(:identity(@identities))
#
changes = exp.csvpaths_reference("*")
changes.set("identities", ids)
changes.name_one(":all():having(:identity(@identities))"):uuid()
#
# get the reference results of executing the expression
#
exp.query()


#
# OR WE COULD JUST SAY....
#
exp = ReferenceExpression.intersect()
exp.set("identities", ids = ["my_validations", "new_validations"])
#
# fails is on left, changes on right
#
fails = exp.results_refrence("$*.csvpaths.:flatten():from(:yesterday()).:identity(@identities)):has_errors():named_paths_uuid()")
changes = exp.csvpaths_reference("$*.csvpaths.:all():having(:identity(@identities))")
#
# get the reference results of executing the expression
#
exp.query()


### THOUGHTS AFTER PSUDEOCODING

I like the plain string version better. Less learning and thinking to do on top of the already complex reference language.




===================

Q: give me all the runs where the named-paths group included a csvpath with the identity "orders"

A: INTERSECT: in results return :named_paths_group() == in csvpaths return :having(:identity(id)) return :named_paths_name()

This uses INTERSECT in order to return the runs, not the instances within the runs. If we wanted to just get the instances we could simply use :having(id) on results. (I realize we'd need to add that function to results, but that is something we should do).


===================

### FOLLOW-UP: add :having() to RESULTS (single-reference, not expression-dependent
-- filters instances/runs by statement identity presence, mirroring CSVPATHS'
own :having()). Noted 2026-08-17, come back to it.


===================

SEMANTICS, SETTLED 2026-08-17 (after working through the "orders" example above):

- The join/comparison key for INTERSECT/SUBTRACT is whatever scalar a side's
  own trailing field accessor resolves to (:identity(), :named_paths_name(),
  :uuid(), :time(), etc) -- NOT path/uuid, which are not comparable across
  datatypes. A side whose reference does not end in a scalar-valued accessor
  (or resolves to a list/dict -- :named_paths_identities(), :file_fingerprints(),
  :scripts()/:webhooks()/:transfers()) is not usable this way; should raise
  clearly rather than fail confusingly deep in a set/dict.
- None-valued keys never match anything, on either side -- excluded from
  membership testing entirely, not treated as equal to each other.
- UNION does NOT correlate the two sides at all -- it is pure concatenation
  of each side's own native ReferenceResults, deduplicated (by full
  ReferenceResult3 equality -- path+uuid+data+identity). It does not use
  the join key, does not filter, does not multiply rows. If the caller wants
  to see which runs pair with which groups, that is done AFTER the union, by
  the caller, walking the combined results and comparing .data values
  themselves -- not something the operation computes. This means there is no
  separate "enumerate all matching pairs" operation needed at all -- UNION,
  used this way, already covers that need.
- INTERSECT/SUBTRACT are filters, not joins that multiply rows -- a left-hand
  ITEM survives (INTERSECT) or is removed (SUBTRACT) based on whether its key
  exists anywhere on the right, regardless of how many right-hand items share
  that key.
  CORRECTED 2026-08-18 (caught by testing, not just design-on-paper): only
  the RIGHT side is reduced to a plain set of keys before the cross-side
  check -- which right-hand item carried a given key never matters, right-
  hand items never appear in the output. The LEFT side must NOT be collapsed
  by key first -- an earlier draft of this doc said "each side is first
  reduced to its own deduplicated set of (key -> item)," which is WRONG for
  the "orders" example itself: if group A has 2 runs and group B has 3, and
  both groups have "orders", INTERSECT must return all 5 runs, not 1 per
  group. Deduping the left side by key would have silently collapsed group
  A's 2 runs and group B's 3 runs down to 1 each. The left side IS still
  deduplicated by full ReferenceResult3 equality first (drops true duplicate
  ITEMS, never a different item that merely shares a key) -- that part is
  always safe. A caller who genuinely wants "one result per distinct key"
  output (the overnight-regression example's own goal, a different question
  than "orders") gets that by calling ReferenceResults3.deduplicated()
  themselves on whichever side needs it before handing it to an expression --
  not something INTERSECT/SUBTRACT force on every use.
- Worked/confirmed example (two groups, "orders" identity, 5 runs total: 2 for
  one group, 3 for the other):
    - both groups' current versions have "orders": UNION of the two sides
      gives 7 ReferenceResults (5 runs + 2 groups).
    - delete one group: 6 ReferenceResults (5 runs still exist -- run history
      does not disappear with the group -- + 1 surviving group); some runs
      now have no matching group in the unioned set.
    - :last() and neither group's CURRENT version has "orders" anymore: 5
      ReferenceResults (all 5 runs, 0 groups) -- every run orphaned.


===================

ARCHITECTURE, SETTLED 2026-08-17:

v3 (the whole csvpath/references/*_3.py system) is not wired into production
yet -- the live managers (results_manager.py, file_manager.py) still dispatch
through the older v2 reference system (csvpath/util/references/). So
ReferenceExpression3 does not need to solve any production-integration
problem -- it can be built and tested the same self-contained way the rest
of v3 has been, no live wiring required yet.

A new ReferenceExpression3 (alongside reference_finder_3.py etc in
csvpath/references/), holding left, op (UNION/SUBTRACT/INTERSECT), right --
each side is either a plain reference string or another ReferenceExpression3
(sub-expressions). Needs two small new pieces that do not exist yet:

1. A "pick the right Finder for this string" dispatcher -- nothing today
   parses a string and automatically routes to Files/Csvpaths/Results
   ReferenceFinder3; every test hand-picks the right one directly.
2. A dedup capability on ReferenceResults3 -- it is currently just a flat
   list, no "give me these with duplicates collapsed" today.

Confirmed:
- Equality for dedup purposes is ReferenceResult3's OWN existing __eq__
  (path + uuid + data + identity) -- identity stays in, it is load-bearing
  for CSVPATHS' statement-range results (no per-statement uuid, only
  identity tells two statements in the same version apart), not just an
  example as first thought.
- UNION uses ONLY that existing equality -- no join-key logic at all, since
  UNION never looks at the key (see SEMANTICS section above).
- INTERSECT/SUBTRACT need a second, different reduction -- CORRECTED
  2026-08-18, see SEMANTICS section above: only the RIGHT side reduces to a
  plain set of resolved keys (dropping None, raising clearly on an
  unhashable one); the LEFT side dedupes by full ReferenceResult3 equality
  only (never by key), then each surviving left ITEM is filtered by whether
  its own key is in the right side's key set.
- ReferenceExpression3 works internally through resolve() only (the join key
  IS resolved data -- no meaningful query()-only mode for INTERSECT/
  SUBTRACT). Output is a flat list of ReferenceResults3, same shape as a
  single reference's results -- each item keeps its own real path/uuid/data
  intact, not collapsed down to just the key used to filter/dedupe. A caller
  who ran the "orders" intersection gets real runs back, with their own
  path/uuid, not just the group-name strings that made them match.

STATUS 2026-08-18: both small pieces built and merged (PR #251) --
ReferenceFinderFactory3.for_reference(), ReferenceResults3.deduplicated().
ReferenceExpression3 itself built on top (reference_expression_3.py) --
resolve()-only, UNION/INTERSECT/SUBTRACT as described above, tested against
David's own "orders" example directly (5/7/6/5 variants all reproduced) plus
the left-side-dedup bug this same pass caught and fixed.

KNOWN GAP, found while building the "orders" test end to end (not a
ReferenceExpression3 problem -- a pre-existing Finder limitation): neither
CsvpathsReferenceFinder3 nor ResultsReferenceFinder3 support root_major='*'
traversal combined with a trailing field accessor today -- both raise
clearly rather than silently doing the wrong thing, but this blocks the
most literal phrasing of "every group"/"every run" without already knowing
the candidate names (i.e. $*.csvpaths.:having("orders"):named_paths_name()
does not work yet). Worked around in the tests via a sub-expression --
UNION of two literal per-group queries -- which is exactly what a caller
can write today once the candidate names are known. Lifting this
restriction (letting '*' traversal resolve a field accessor per matched
group/run) would make reference expressions' own most natural use case --
searching across unknown groups/runs -- actually reachable; worth
prioritizing before reference expressions goes much further, since without
it every expression needs already-known root_major names on both sides,
which undercuts a lot of the point.

FIXED 2026-08-18 (PR #253, branch feature/references-v3-star-traversal-
field-accessors, branched fresh off main after #251 merged, independent of
#252 which was still open): both Finders now allow a field accessor
alongside the pointer in '*' traversal. RESULTS needed only the guard
loosened -- field-accessor resolution already read from the matched run's
own real directory, independent of group. CSVPATHS needed a real fix:
added _group_manifest_entry(root_major, uuid), which searches every named-
paths group's manifest for the matching uuid when root_major is '*'
(uuids assumed globally unique), returning (group_name, entry) -- used for
both manifest-sourced and definition.json-backed fields. Also caught, while
verifying RESULTS, a separate previously-latent bug: _extract_data's star-
traversal branch checked isinstance(root_major, Star3) unconditionally, so
a bare-pointer resolve() (no :manifest()) incorrectly took the global-
ledger-by-uuid path instead of falling through to None -- no existing test
had ever called resolve() (only query()) on a bare star-traversal reference
before this. Full suite 2635 passed, known 11-failure baseline. #253
merged.

FOLLOW-UP DONE 2026-08-18: merged main into #252's own branch to pick up
#253, then updated test_reference_expression_3.py's
TestStarTraversalPlusFieldAccessorIsNotYetSupported. Confirmed LIVE, before
touching anything, that its two original tests still passed post-merge but
for a DIFFERENT, narrower reason than before -- CSVPATHS' ":having()" is
neither a pointer nor ":all()", so it now falls through to an unrelated
"requires a pointer" rejection; RESULTS' ":flatten()" still has its own
explicit, separate rejection. #253 only fixed a field accessor riding
alongside a bare pointer/":all()" -- neither ":having()" nor ":flatten()"
combined with '*' traversal is supported yet, a real, still-open, narrower
gap. Renamed the class to TestStarTraversalPlusFieldAccessorNowWorks and
replaced its tests with positive ones proving a star-rooted reference
STRING now resolves end to end through ReferenceExpression3 (both CSVPATHS
":all():named_paths_name()" and RESULTS ":last():named_paths_name()").
Kept the original two raise-asserting tests too, moved to a new
TestHavingAndFlattenPlusStarTraversalStillNotSupported class with
corrected comments -- this is exactly why the "orders" example's own
_left_side/_right_side helpers STILL need the sub-expression workaround on
both sides even after #253: RESULTS' "every run" needs
:flatten()+field-accessor, CSVPATHS' "every group with an orders
statement" needs :having()+field-accessor, and neither of those specific
combinations is what #253 fixed. Pushed to #252's branch (still open, not
yet reviewed); full suite 2661 passed, known 11-failure baseline.

FIXED 2026-08-18 (PR #254, branch feature/references-v3-star-traversal-
having-flatten, branched fresh off main after #253 merged): closed BOTH
of those narrower gaps.
- CSVPATHS: :having("identity") now filters each group's manifest before
  either mode's pointer/grouping reduction, mirroring _resolve_versions()'s
  single-group precedent. This was a real, previously-latent bug, not
  just unbuilt: :having() was never checked for at all in
  _query_star_traversal before this fix -- confirmed live that
  "$*.csvpaths.:all():having('orders')" silently returned every group's
  every version, UNFILTERED, before the fix. A bare :having() alone (no
  pointer/:all()) still raises "requires a pointer" on purpose -- no new
  "unreduced flatten" meaning invented.
- RESULTS: :flatten() now pools every group's runs at any depth (not the
  zero-level-only restriction a bare pointer keeps) before the pointer
  reduces it -- _discover_run_homes(None) already discovers any-depth
  across every group, so only routing to it (instead of the zero-level-
  filtered set) was needed.
Both compose cleanly with #253's field accessor. tests/references/ 1055
passed, full suite 2643 passed, known 11-failure baseline. PR #254 open,
not yet reviewed.

STILL TRUE FOLLOW-UP: #252's own test_reference_expression_3.py
_left_side/_right_side helpers still use the sub-expression workaround --
now that BOTH underlying gaps are closed (once #254 merges and is pulled
into #252's branch, same pattern as #253's merge), they could switch to
real '*' traversal on both sides. Worth confirming the "orders" numbers
(7/6/5 UNION, 5/2/0 INTERSECT) come out identical either way before
removing the workaround, not just assuming.

THIRD GAP FOUND AND FIXED 2026-08-19, same PR #254 (addendum commit
c57f5d59): while documenting #254's own top-of-file docstring restriction
("still no path narrowing/:all()/name_three/:manifest()"), David asked
for a clearer explanation of the ':all()' exclusion specifically. That
surfaced a real, unresolved MEANING COLLISION, not just an unbuilt
feature -- see "THE ':all()' MEANING COLLISION AT STAR TRAVERSAL" in
normative_reference_examples.txt (added 2026-08-19, worked example with
concrete data, at David's request for examples over narrative) for the
full worked-through decision. Resolved: David confirmed interpretation 3
(partition by the COMPOSITE (named-results-group, template-value) key),
matching FilesReferenceFinder3's own already-built ':all()' precedent
exactly. Implemented in ResultsReferenceFinder3._query_star_traversal --
partitions every one-level candidate by (group, _group_key(rh, that
group's own home)), reduces each partition independently by the pointer.
':all()'/':flatten()' stay mutually exclusive; ':all()' composes with the
#253 field accessor same as ':flatten()' does. tests/references/ 1057
passed, full suite 2645 passed, known 11-failure baseline. PR #254
retitled to "Support :having()/:flatten()/:all() combined with '*'
traversal" to reflect the expanded scope, still open, not yet reviewed.

FOURTH+FIFTH GAPS FOUND AND FIXED 2026-08-19, same PR #254 (addendum
commit 216b2675): David read the docstring's remaining restriction list
("still no literal/'*' path narrowing, no name_three, no :manifest()")
and asked for a breakdown of what each would take. Turned out path
narrowing and name_three were much cheaper than the docstring implied --
both mechanical generalizations of building blocks #253/#254's own work
already built, not genuinely new design questions:
- path narrowing: _compile_path_pattern()/_matches_prefix()/
  _matches_prefix_at_least()/_group_key() are all shared helpers already
  built for the literal-root case -- the exact same "per-candidate-own-
  group-home instead of one fixed home" generalization already applied
  three times (zero-level bare pointer, ':flatten()', ':all()').
- name_three: _results_for_run() already does the identity/':all()'/
  range selection entirely from a real run directory, independent of
  group -- composes with every shape once identity/match_all/
  range_bounds/accessor are threaded through, same as the field accessor
  did in #253.
:manifest() is the one still genuinely deferred -- see the THIRD-gap
entry above and _extract_data()'s own has_manifest comment for why (a
real ambiguity between a Rule-1a/1b global-ledger result and a
traversal-selected run directory, not solved here).

Restructured _query_star_traversal to mirror query()'s own FULL dispatch
tree (bare / prefix+':flatten()' / prefix+':all()' / prefix+':groups()'
[still deferred] / plain literal path), instead of rejecting anything but
the bare shape outright. Factored the by-then-repeated validation/reduce
logic into three shared helpers: _star_run_selector_chain(),
_star_pool_and_reduce(), _star_group_and_reduce().

David also asked to confirm his own reading of the name_three + ':all()'
grouping interaction directly: "$*.results.:all():last().invoices:uuid()
can find multiple runs resulting in multiple invoices csvpaths
statements, each of which has a UUID... a list of zero or more UUID."
Confirmed correct -- and confirmed live before writing anything that this
exact shape (grouping + a name_three FIELD accessor) already worked at
the literal-root level (":all():last().invoices:uuid()" resolves fine,
poolable) while a name_three CONTENT accessor (":errors()" etc) in the
same grouped position is REJECTED at the literal-root level too -- so
_star_group_and_reduce() mirrors that exact distinction rather than
inventing new semantics.

tests/references/ 1065 passed, full suite 2653 passed, known 11-failure
baseline. PR #254 retitled to "Support :having()/:flatten()/:all()/path-
narrowing/name_three combined with '*' traversal", still open, not yet
reviewed. David's plan going forward: merge #254, pull it into #252's
branch (same pattern as #253), get #252 merged and closed, THEN open a
new branch for the :manifest() gap.

#254 MERGED AND CLOSED 2026-08-19. Pulled into #252's branch (clean
merge, tests/references/ 1091 passed immediately after) to make the
switch to real '*' traversal on both sides of the "orders" example, per
David's instruction ("make the updates required").

CSVPATHS' right side was ready immediately (':all()' with no pointer
already listed everything per group, unreduced -- pre-existing
CsvpathsReferenceFinder3 precedent, confirmed live). RESULTS' left side
was NOT -- discovered live (before writing anything) that
ResultsReferenceFinder3._query_star_traversal STILL unconditionally
required a pointer in every shape, which blocks "every run, unreduced"
entirely -- exactly what the RESULTS side needs.

David explicitly asked, before authorizing a fix: "will that leave any
gaps or inconsistencies with files, the datatype most like results?" --
investigated precisely rather than assuming:
- RESULTS' own literal-root query() never requires a pointer, any shape
  -- the exact capability the old sub-expression workaround relied on.
- FilesReferenceFinder3's '*' traversal never requires a pointer either,
  in any of its four modes (confirmed by re-reading its actual code, not
  memory) -- a missing pointer there returns a deduped file_home list.
- CsvpathsReferenceFinder3's '*' traversal is the ACTUAL OUTLIER here,
  not the target precedent as I had been assuming while building the
  :having()/:flatten()/:all() work: pointer required in POOL/flatten
  mode, optional only in GROUP/':all()' mode.

FIXED 2026-08-19 (same #252 branch, commit c65373b9): made RESULTS' star
traversal match its own literal-root precedent and FILES (both fully
optional) rather than CSVPATHS' narrower one -- a pointer is now
optional in EVERY RESULTS '*'-traversal shape (bare/':flatten()'/
':all()'/literal-prefixed alike); absence means every matched run comes
back unreduced. No FILES-style dedup/uuid=None trick needed -- RESULTS'
own _discover_run_homes() already dedupes by run directory, so every
unreduced result can carry its own real uuid. The existing "more than
one candidate + name_three content accessor" guard (built for ':all()'
grouping) now also covers the no-pointer POOL case, since it too can
yield more than one run. CSVPATHS' own asymmetric rule was deliberately
left untouched -- a separate, already-merged PR, not blocking anything
needed here.

_left_side/_right_side in test_reference_expression_3.py are now each a
single plain reference string (no more ReferenceExpression3 sub-
expression wrapping either side). Confirmed the "orders" example's
documented 7/6/5 UNION / 5/2/0 INTERSECT numbers come out IDENTICAL with
real traversal -- TestOrdersExampleEndToEnd's own assertions, completely
unchanged, still pass -- resolving the "worth confirming... not just
assuming" follow-up noted after #254's own earlier addendum.
TestHavingAndFlattenPlusStarTraversalStillNotSupported (both cases
raised) replaced with TestHavingAndFlattenPlusStarTraversalNowWork (both
resolve) -- including a UNION-with-a-literal-root-duplicate test that
caught a real math mistake in my own first draft (I initially asserted
naive pooled counts, e.g. 6 runs for a UNION where 2 items are identical
across both sides -- ReferenceResults3's dedup correctly collapses those
to 5, confirmed by running the test and letting it fail before
correcting the assertion, not just reasoning it out on paper).

tests/references/ 1097 passed, full suite 2685 passed, known 11-failure
baseline. PR #252 updated (commit c65373b9 pushed, detailed PR comment
posted), ready to merge. David's plan going forward: merge #252, THEN
open a new branch for the :manifest() gap (the last of the originally-
identified three star-traversal restrictions).

CSVPATHS' OWN POINTER-OPTIONALITY GAP CLOSED TOO, 2026-08-19, same PR
#252 branch (commit 8513cac2). While reviewing #252, David asked
directly whether to fix CSVPATHS' own remaining pointer-required-in-
POOL-mode inconsistency now (the one I had explicitly left untouched)
rather than push it to yet another branch -- his own framing: "all else
being equal I would just fix it here and be done with this area
cleanly." Agreed it was small/low-risk (unlike :manifest(), which stays
genuinely deferred) and fixed it: CsvpathsReferenceFinder3's own POOL/
flatten mode now also allows no-pointer, listing every candidate across
every group unreduced, matching its own GROUP/':all()' mode's existing
no-pointer precedent and RESULTS' equivalent fix.

A SECOND, real, previously-latent bug surfaced while making this exact
change, not just a stale test: the "is this combination supported"
check was a BLACKLIST (any(name=="manifest") or any(name in
("from","to"))), not a whitelist -- confirmed live that ":definition()"
(a real, registered CSVPATHS function) silently fell through unrejected
once the "no pointer" rule stopped masking it by forcing an unrelated
raise first. Fixed by switching to the same whitelist pattern RESULTS'
own _star_run_selector_chain() already established (explicitly
enumerate pointer/':all()'/':having()'/field-accessor as the only legal
extras, reject everything else) -- closes the gap generally, confirmed
via ':groups()' too (not registered for CSVPATHS but still build-chain-
able, now correctly rejected).

tests/references/ 1099 passed, full suite 2687 passed, known 11-failure
baseline. This closes out star-traversal pointer-optionality across all
three datatypes cleanly, as David wanted. Only :manifest() remains,
still planned for its own fresh branch after #252 merges.

