from ...reference_3 import Reference3
from ..function_3 import Function3


class Fingerprint3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    #
    # KIND = "fingerprint" (added 2026-08-26, revised same day from an
    # initial "leave uncategorized" call -- see ReferenceExpression3's
    # own UNION-compatibility notes): a fingerprint is a cryptographic
    # identity of BYTES, not of an entity/event the way a uuid is --
    # two fingerprints being equal means "the same content," full stop,
    # regardless of which manifest field recorded it or which distinct
    # entity that field belongs to. David's own worked case: a named-
    # paths group's own content (this function) legitimately compares
    # against a run's own record of which named-paths content drove it
    # (a field the run manifest does not carry yet, but should --
    # tracked on the deferred-work bucket list) -- something :uuid()
    # cannot do, since two groups loaded from identical group.csvpaths
    # text under different names get different uuids but identical
    # fingerprints. Grouped with the Results Run Manifest's own
    # named_file_fingerprint and the Result Instance Manifest's own
    # file_fingerprints under this same KIND for exactly that reason,
    # even though each describes a different entity's content -- the
    # conceptual purpose (byte-identity) is what UNION compares, not
    # which entity happens to own the field.
    #
    # ARG_TYPES accepts an optional str -- added 2026-08-13, for FILES
    # only, to support the bare-lookup shape
    # ("$alpha.files.:fingerprint('hash...')", no :name(...) needed):
    # search the WHOLE named-file's manifest for the entry whose own
    # fingerprint matches, since content-hash identity does not care
    # which file/path slot a version happens to be registered under
    # (unlike :name(), which matches file_home, a path identity). This
    # class's own ROLE stays VALUE (unchanged) specifically so it keeps
    # NOT counting as a second pointer when it rides alongside a real
    # one in its ordinary field-accessor position (e.g.
    # ":name('orders.csv').:first():fingerprint()"); the bare-lookup
    # shape is instead recognized declaratively via SELECTOR_WHEN_ARGUED
    # (added 2026-08-28, replacing the original bespoke, hand-written
    # FilesReferenceFinder3._is_bare_fingerprint_reference() check -- see
    # ReferenceFinder3._is_bare_selector_reference() for the shared
    # mechanism this and any future selector-when-argued function now
    # go through).
    #
    SELECTOR_WHEN_ARGUED = True
    #
    # CORRECTED 2026-10-18: this docstring used to claim "CSVPATHS has
    # no bare-lookup shape (that's FILES-only)" -- that was true when
    # written (2026-08-13), but went stale once CsvpathsReferenceFinder3
    # grew its own `_is_bare_selector_reference()` dispatch branch for
    # :uuid()'s own cross-datatype build (2026-10-18). That dispatch is
    # GENERIC (keyed on SELECTOR_WHEN_ARGUED, not hardcoded to "uuid"),
    # so it picked this function up too, for free -- confirmed live,
    # surfaced by an automated cross-datatype consistency sweep, NOT
    # something anyone deliberately decided at the time. David's own
    # call once flagged (2026-10-18): keep it -- CSVPATHS versions
    # genuinely ARE fingerprinted (same KEY entry below), so "select a
    # named-paths group version by its own content hash" is exactly as
    # coherent a thing to want as the FILES case already built for.
    # ":fingerprint()" now has the bare-lookup shape for BOTH FILES and
    # CSVPATHS, not FILES-only.
    #
    NAME = "fingerprint"
    SUMMARY = (
        "The content-integrity hash of the resolved named-file/named-"
        "paths version's own defining content (the file's bytes, or "
        "group.csvpaths' text) -- SHA256 in most cases; S3-backed "
        "content uses MD5 instead, per the same fingerprint mechanism "
        "used throughout the framework. Also usable bare, for both "
        "FILES and CSVPATHS, with a known hash to look up the "
        "specific version it identifies, across every path/version "
        "under the resolved named-entity."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "fingerprint"
    KEY = {
        Reference3.FILES: "fingerprint",
        Reference3.CSVPATHS: "fingerprint",
    }
    #
    # CSVPATHS' own name_one is ALWAYS the version-selecting function
    # chain (there is no separate name_three position the way FILES
    # has), so POSITIONS alone cannot distinguish "bare selector, sole
    # content, no pointer" from "ordinary field-accessor chained
    # alongside a pointer" the way FILES' own two-position declaration
    # does -- both shapes share the identical NAME_ONE position here.
    # The SHAPE itself (sole path element + an argument + no pointer)
    # is what `_is_bare_selector_reference()` keys on instead; see its
    # own docstring.
    #
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
    }
