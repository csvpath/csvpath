from .csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
from .files_reference_finder_3 import FilesReferenceFinder3
from .reference_3 import Reference3
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_3 import ReferenceFinder3
from .reference_parser_3 import ReferenceParser3
from .results_reference_finder_3 import ResultsReferenceFinder3


class ReferenceFinderFactory3:
    #
    # given a raw reference string, picks and constructs the right
    # ReferenceFinder3 subclass for its own datatype -- nothing did this
    # automatically before (every test, and every real usage so far,
    # hand-picks Files/Csvpaths/ResultsReferenceFinder3 directly). Built
    # for ReferenceExpression3, whose two sides are each just a plain
    # reference string that could be any of the three datatypes -- see
    # references_notes/notes/reference_expressions_notes.txt's own
    # ARCHITECTURE section. Mirrors ReferenceFunctionFactory's own
    # name-keyed dispatch shape (reference_function_factory_3.py), just
    # keyed on datatype instead of function name.
    #
    _FINDERS = {
        Reference3.FILES: FilesReferenceFinder3,
        Reference3.CSVPATHS: CsvpathsReferenceFinder3,
        Reference3.RESULTS: ResultsReferenceFinder3,
    }

    @classmethod
    def for_reference(cls, *, reference: str, csvpaths) -> ReferenceFinder3:
        """parses `reference` and returns a real ReferenceFinder3 for
        whichever datatype it turns out to be. Reference3's own
        constructor already guarantees datatype is one of FILES/
        CSVPATHS/RESULTS (raises ValueError otherwise, at parse time) --
        the lookup below cannot actually miss today, but stays a real
        checked dispatch rather than a bare index, so a future fourth
        datatype fails here clearly instead of deeper inside whichever
        Finder class happens to get picked by accident."""
        if not reference:
            raise ValueError("ReferenceFinderFactory3 reference cannot be None or empty")
        if csvpaths is None:
            raise ValueError("ReferenceFinderFactory3 csvpaths cannot be None")
        ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
        finder_cls = cls._FINDERS.get(ref.parsed.datatype)
        if finder_cls is None:
            raise ReferenceException3(
                f"ReferenceFinderFactory3 has no ReferenceFinder3 registered "
                f"for datatype {ref.parsed.datatype!r}."
            )
        return finder_cls(csvpaths=csvpaths, ref=ref)
