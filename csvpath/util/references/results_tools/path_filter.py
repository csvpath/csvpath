import os
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.results_tools.date_filter import DateFilter


class PathFilter:
    @classmethod
    def update(cls, results: ReferenceResults) -> None:
        ref = results.ref
        name = ref.name_one
        if name is None:
            return
        if DateFilter.is_date(name):
            return
        filtered = []
        archive = results.csvpaths.config.get(section="results", name="archive")
        pre = os.path.join(archive, ref.root_major)
        pre = os.path.join(pre, name)
        #
        # after these two joins what is the risk of windows seps in cloud paths?
        # will nos account for that? nos does, but worth remembering this point.
        #
        for _ in results.files:
            #
            # should be prefixed by archive path or not? seems like it should be.
            # the tests will tell us.
            #
            if _.startswith(pre):
                filtered.append(_)
        results.files = filtered
