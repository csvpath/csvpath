import os
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.results_tools.date_filter import DateFilter


class PathFilter:

    #
    # we return False if we cannot match anything. that tells the finder
    # try a date filter. if we match anything the results.files list is
    # filtered down and we return True to indicate that the date filter is
    # not needed.
    #
    # we shortcut our filter process by asking the datefilter if name_one
    # is a date. if it is, we can return False to indicate that the
    # DateFilter should handle it. not sure I like this approach.
    #
    @classmethod
    def update(cls, results: ReferenceResults) -> bool:
        ref = results.ref
        name = ref.name_one
        if name is None:
            return
        filtered = []
        archive = results.csvpaths.config.get(section="results", name="archive")
        pre = os.path.join(archive, ref.root_major)
        pre = os.path.join(pre, name)
        #
        # after these two joins what is the risk of windows seps in cloud paths?
        # will nos account for that? nos does, but worth remembering this point.
        #
        found = False
        for _ in results.files:
            #
            # should be prefixed by archive path or not? seems like it should be.
            # the tests will tell us.
            #
            if _.startswith(pre):
                filtered.append(_)
                found = True
        if len(filtered) > 0:
            results.files = filtered
        return found
