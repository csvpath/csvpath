import os
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.reference_parser import ReferenceParser


class PossiblesResolver:
    @classmethod
    def update(self, *, results: ReferenceResults) -> str:
        ref = results.ref
        #
        # the results home + template itself only tells you the filenames if
        # you count separators and list all the possible dirs, which only gets
        # you the same thing.
        #
        # also worth noting: if the template changes we cannot resolve the
        # earlier runs unless we set it back. this is a weakness we can address
        # but not atm.
        #
        mani = results.runs_manifest
        #
        # for our named-results
        #
        possibles = []
        for m in mani:
            npn = m["named_paths_name"]
            if npn.startswith("$"):
                ref_x = ReferenceParser(string=npn, csvpaths=results.csvpaths)
                if ref_x.root_major == ref.root_major:
                    if m["run_home"] not in possibles:
                        possibles.append(m["run_home"])
            elif m["named_paths_name"] == ref.root_major:
                if m["run_home"] not in possibles:
                    possibles.append(m["run_home"])
            else:
                ...

        results.files = possibles
