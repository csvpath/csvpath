import os
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.reference_exceptions import ReferenceException


class DataFinder:
    @classmethod
    def update(self, *, results: ReferenceResults) -> None:
        if len(results.ref.name_three_tokens) != 1:
            return
        if len(results.files) > 1:
            #
            # if we're looking for 1 thing (data or unmatched) in the context
            # of 1 thing (a results ref with name_three pointing at an instance)
            # and we find that we're in the context of >1 things (multiple
            # instances), then we don't find anything.
            #
            results.files = []
            return
            """
            raise ReferenceException(
                "Cannot use data from more than one set of results"
            )
            """
        if len(results.files) == 0:
            return
        n = results.ref.name_three_tokens[0]
        results.files = [os.path.join(results.files[0], f"{n}.csv")]
