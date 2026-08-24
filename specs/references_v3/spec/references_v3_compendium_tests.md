# References v3 Compendium — Test Conformance Map

Maps each numbered item in `references_v3_compendium.md` (`#### N.M`
headings) to the test(s) that verify it. Built and kept current during
Phase 1 of `specs/references_v3/notes/rc_roadmap.md` (the block-by-block
compendium review), not all at once up front.

**Conventions:**
- One `#### N.M` heading per compendium item, in the same order as the
  compendium itself.
- Below each, a bullet list of `test_file.py::TestClass::test_method`
  references that verify it. Many-to-many is normal and expected -- an
  item may need several tests to cover fully (e.g. one per datatype row
  in a table), and one test may verify several items at once; list it
  under each item it actually covers, don't force a false 1:1.
- An item with no test yet is marked explicitly, `- *(no test yet)*` --
  never leave it silently blank. A visible gap here is exactly the
  "tests needed" signal Phase 1 is supposed to produce, and doubles as a
  live view into how much of the compendium is actually proven versus
  just asserted.
- Kept as a separate file from the compendium on purpose (David,
  2026-08-24) -- keeps the compendium itself concise and readable as pure
  directive requirements, while still letting every claim be traced to
  real, running proof.

---
