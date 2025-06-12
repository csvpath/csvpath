# pylint: disable=C0114
# from csvpath import CsvPaths
from .reference_parser import ReferenceParser
from .reference_results import ReferenceResults
from .files_tools.fingerprint_finder import FingerprintFinder
from .files_tools.all_arrivals import AllArrivals
from .files_tools.possible_filenames import PossibleFilenames
from .files_tools.date_finder import DateFinder
from .files_tools.token_filters import TokenFilters
from .files_tools.manifest_order import ManifestOrder


class FilesReferenceFinder2:
    # csvpaths: "CsvPaths" due to flake
    def __init__(
        self, csvpaths, *, ref: ReferenceParser = None, reference: str = None
    ) -> None:
        self._csvpaths = csvpaths
        self.reference = reference
        self._ref = None
        if self.reference is not None:
            if ref is not None:
                raise ValueError("Cannot provide both ref and name")
            self._ref = ReferenceParser(reference)
        if self._ref is None:
            self._ref = ref
        if reference is None:
            self.reference = ref.ref_string

    @property
    def ref(self) -> ReferenceParser:
        return self._ref

    # csvpaths(self) -> "CsvPaths" disallowed by flake
    @property
    def csvpaths(self):
        return self._csvpaths

    @property
    def manifest(self) -> list:
        results = ReferenceResults(ref=self.ref, csvpaths=self.csvpaths)
        mani = results.manifest
        return mani

    def resolve(self) -> list:
        lst = self.query().files
        return lst

    def query(self) -> ReferenceResults:
        #
        # everything happens through the results object
        #
        results = ReferenceResults(ref=self.ref, csvpaths=self.csvpaths)
        #
        # fingerprint
        #
        FingerprintFinder.update(results)
        print(f"query: files 0: {len(results)}")
        if len(results) > 0:
            return results
        #
        # all arrivals gets every possible file, but only if name_one is empty
        #
        AllArrivals.update(results)
        print(f"query: files 1: {len(results)}")
        #
        # filenames that match name_one
        #
        PossibleFilenames.update(results)
        print(f"query: files 2: {len(results)}")
        #
        # files that match a date in name_one. we have to pass the tokens
        # because we are looking for a range that may be determined by tokens, rather
        # than the tokens filtering the results. i.e. if we have a date we must be
        # interested in before the date or after it.
        #
        DateFinder.update(results, self.ref.name_one, self.ref.name_one_tokens)
        print(f"query: files 3: {len(results)}")
        #
        # indexes, first, last require manifest arrival order.
        #
        ManifestOrder.update(results)
        print(f"query: files 4: {len(results)}")
        #
        # filter for all tokens, incl. datetime tokens and indexes
        #
        TokenFilters.update(results, self.ref.name_one_tokens)
        print(f"query: files 5: {len(results)}")
        #
        # files that match a date in name_three
        #
        DateFinder.update(
            results, self.ref.name_three, self.ref.name_three_tokens, filter=True
        )
        print(f"query: files 6: {len(results)}")
        #
        # filter for all tokens, incl. datetimes and indexes
        #
        TokenFilters.update(results, self.ref.name_three_tokens)
        print(f"query: files 7: {len(results)}")
        #
        #
        #
        return results
