# pylint: disable=C0114
import os
import json
from datetime import datetime
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..nos import Nos
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.ref_utils import ReferenceUtility as refu
from csvpath.util.references.results_tools.resolve_possibles import PossiblesResolver
from csvpath.util.references.results_tools.path_filter import PathFilter
from csvpath.util.references.results_tools.date_filter import DateFilter
from csvpath.util.references.results_tools.token_filters import TokenFilters
from csvpath.util.references.results_tools.identity_finder import IdentityFinder
from csvpath.util.references.results_tools.data_finder import DataFinder
from csvpath.util.references.results_tools.yesterday_or_today_translator import (
    YesterdayOrTodayTranslator,
)


class ResultsReferenceFinder2:

    # csvpaths == csvpaths:"CsvPaths" which is disallowed by flake
    def __init__(
        self, csvpaths, *, ref: ReferenceParser = None, reference: str = None
    ) -> None:
        self.reference: str = None
        self._csvpaths = csvpaths
        self._ref = ref
        if reference is not None:
            if ref is not None:
                raise ValueError("Cannot provide both ref and name")
            self._ref = ReferenceParser(reference, csvpaths=self.csvpaths)
        #
        # we need to know the os path segment separator to use. if
        # we're working on a config.ini that points to a cloud service
        # for [results]archive then we're always '/'.
        #
        self.sep = (
            csvpaths.config.get(section="results", name="archive").find("://") > -1
        )
        self.sep = "/" if self.sep is True or os.sep == "/" else "\\"

    @property
    def ref(self) -> ReferenceParser:
        return self._ref

    #  -> "CsvPaths" due to flake
    @property
    def csvpaths(self):
        return self._csvpaths

    def resolve(self) -> list:
        lst = self.query().files
        return lst

    def query(self) -> ReferenceResults:
        if self.ref is None:
            refstr = self.reference
            #
            # translate yesterday and today
            #
            if refstr.find("yesterday") > -1 or refstr.find("today") > -1:
                return YesterdayOrTodayTranslator.update(finder=self, refstr=refstr)
            #
            #
            #
            # print(f"ResultsRefFinder: query: 1")
            self._ref = ReferenceParser(refstr, csvpaths=self.csvpaths)
        # print(f"ResultsRefFinder: query: 2")
        results = ReferenceResults(ref=self.ref, csvpaths=self.csvpaths)
        #
        # find possibles based on path, date, index
        #
        # print(f"ResultsRefFinder: query: 3: results: {len(results)}")
        PossiblesResolver.update(results=results)
        #
        # at this point we have paths that include the archive?
        #
        ...
        #
        # 2. path. with templates the path to the run dir can vary
        # 3. date string
        #
        # if the path matches anyting we don't use the date. but if the
        # path doesn't match and the date isn't a date the query found
        # nothing. if the path finds nothing but the date is a date
        # DateFilter trims the possibles.
        #
        # print(f"ResultsRefFinder: query: 4: results: {len(results)}")
        if PathFilter.update(results) is False:
            # print(f"ResultsRefFinder: query: 5: results: {len(results)}")
            DateFilter.update(
                results,
                name_or_token=results.ref.name_one,
                tokens=results.ref.name_one_tokens,
            )
        #
        # filter using name_one's up to 2 tokens
        #
        # _ = self.ref if self.reference is None else self.reference
        # print(f"ResultsRefFinder: query: 6: results: {len(results)}: {_}")
        TokenFilters.update(results=results, tokens=self.ref.name_one_tokens)
        #
        # point to csvpath identity
        #
        # print(f"ResultsRefFinder: query: 7: results: {len(results)}")
        if self.ref.name_three is not None:
            IdentityFinder.update(results=results)
            # print(f"ResultsRefFinder: query: 8: results: {len(results)}")
            DataFinder.update(results=results)
        #
        # point to output file
        #
        # STOP HERE for finding data files using this class
        #
        self._assure_archive_root(results)
        #
        # because files can be deleted while the manifest stays the same we
        # have to double check results. this is expensive. in the future we might
        # update the manifest entries to mark them deleted, thereby avoiding
        # the double check.
        #
        # we do this in find possibles and date filter. we shouldn't need to do
        # it again here.
        #
        """
        __ = []
        if results.files:
            for _ in results.files:
                nos = Nos(_)
                if nos.dir_exists():
                    print(f" ... {_} exists")
                    __.append(_)
                else:
                    print(f" ... {_} does not exist")
            results.files = __
        """
        return results
        #
        #
        # but in future within a function we could go one step further:
        #
        #   $myresults.results.Acme/orders:last.identity3:data:myheadername
        #   $myresults.results.2025-01-:last.identity3:data:myheadername
        #   $myresults.results.:12.identity3:data:myheadername
        #   $myresults.results.Acme/orders:last.identity3:variables:myvarname
        #
        # ...
        #
        # point to var/metatdata field/header
        #

    def _assure_archive_root(self, results) -> None:
        assured = []
        archive = self.csvpaths.config.get(section="results", name="archive")
        resname = self.ref.root_major

        ar = os.path.join(archive, resname)

        for _ in results.files:
            if not _.startswith(ar):
                if _.startswith(self.ref.root_major):
                    _ = os.path.join(archive, _)
                else:
                    _ = os.path.join(ar, _)
            assured.append(_)
        results.files = assured
