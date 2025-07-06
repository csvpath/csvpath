# pylint: disable=C0114
import os
import json
from datetime import datetime
from csvpath.util.file_readers import DataFileReader
from csvpath.util.references.results_reference_finder_2 import (
    ResultsReferenceFinder2 as ResultsReferenceFinder,
)
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.reference_exceptions import ReferenceException
from csvpath.util.references.files_reference_finder_2 import (
    FilesReferenceFinder2 as FilesReferenceFinder,
)


class ReferenceManifestEntryFinder:
    def __init__(self, csvpaths, *, ref: ReferenceParser = None, name=None) -> None:
        self._csvpaths = csvpaths
        self._name = name
        self._ref = None
        if self._name is not None:
            if ref is not None:
                raise ValueError("Cannot provide both ref and name")
            self._ref = ReferenceParser(name, csvpaths=self.csvpaths)
        if self._ref is None:
            self._ref = ref
        self.reference = name

    @property
    def ref(self) -> ReferenceParser:
        return self._ref

    @property
    def csvpaths(self):
        return self._csvpaths

    def get_file_manifest_entry_for_results_reference(self, reference=None) -> dict:
        results = ResultsReferenceFinder(
            self.csvpaths,
            reference=reference if reference is not None else self.reference,
        ).query()
        if len(results.files) > 1:
            raise ReferenceException(
                "Expecting only one result path, not {len(results.files)}"
            )
        if len(results.files) == 0:
            #
            # is this unusual?
            #
            return None
        home = results.files[0]
        mpath = os.path.join(home, "manifest.json")
        mani = None
        with DataFileReader(mpath) as reader:
            mani = json.load(reader.source)
        #
        # if we're looking at a ref with a name_three pointing at a csvpath identity the
        # manifest is that instance's. if so, we need to look for "actual_data_file", not
        # named_file_path. usually these will point to the same place; however, in the
        # case of source-mode: preceding they would not be the same.
        #
        file = None
        if "named_file_path" in mani:
            file = mani["named_file_path"]
        elif "actual_data_file" in mani:
            file = mani["actual_data_file"]
        nfn = mani["named_file_name"]
        if nfn.startswith("$"):
            ref = ReferenceParser(nfn, csvpaths=self._csvpaths)
            if ref.datatype == ref.FILES:
                # file ref? use files_refer_finder.get_manifest_entry_for_reference
                return self.get_file_manifest_entry_for_reference(ref=ref)
            elif ref.datatype == ref.RESULTS:
                # results ref? use this method recursively
                return self.get_file_manifest_entry_for_results_reference(reference=nfn)
        else:
            # plain nfn? do this:
            mani = self._csvpaths.file_manager.get_manifest(nfn)
            for _ in mani:
                if _["file"] == file:
                    return _
        raise ValueError(
            f"Cannot match reference {self.ref.reference} pointing to file {file} to a manifest entry"
        )

    #
    # used by results reference finder and run home maker
    #
    def get_file_manifest_entry_for_reference(self, ref=None) -> dict:
        ref = ref if ref is not None else self.ref
        finder = FilesReferenceFinder(ref=ref, csvpaths=self.csvpaths)
        results = finder.query()
        mani = results.manifest
        files = results.files
        file = None if len(files) == 0 else files[0]
        for _ in mani:
            path = _["file"]
            if file == path:
                return _
        raise ValueError(
            f"Cannot match reference {self.ref.ref_string} pointing to file {file} to a manifest entry"
        )
