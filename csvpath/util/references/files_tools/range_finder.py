from csvpath.util.date_util import DateUtility as daut
from csvpath.util.references.reference_results import ReferenceResults


class RangeFinder:
    @classmethod
    def for_token(
        cls, results: ReferenceResults, *, adate, token: str, filter=False
    ) -> list:
        #
        # filter == True is to thin out results.files
        # filter == False is to pull in from manifest.json
        #
        #
        # should we be supporting from and to?
        #
        if token not in ["after", "before"]:
            raise ValueError("token must be after or before")
        if token == "after":
            return cls.all_after(results, adate, filter=filter)
        elif token == "before":
            return cls.all_before(results, adate, filter=filter)

    @classmethod
    def all_after(cls, results: ReferenceResults, adate, filter=False) -> list:
        #
        # filter == True is to thin out results.files
        # filter == False is to pull in from manifest.json
        #
        lst = []
        for t in results.manifest:
            if not filter or t["file"] in results.files:
                lst.append(t["time"])
        lst2 = daut.all_after(adate, lst)
        lst3 = []
        for i, t in enumerate(lst2):
            if t is not None:
                lst3.append(results.manifest[i]["file"])
        return lst3

    @classmethod
    def all_before(cls, results: ReferenceResults, adate, filter=False) -> list:
        #
        # filter == True is to thin out results.files
        # filter == False is to pull in from manifest.json
        #
        lst = []
        for t in results.manifest:
            if not filter or t["file"] in results.files:
                lst.append(t["time"])
        lst2 = daut.all_before(adate, lst)
        lst3 = []
        for i, t in enumerate(lst2):
            if t is not None:
                lst3.append(results.manifest[i]["file"])
        return lst3
