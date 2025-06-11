import os
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.matching.util.expression_utility import ExpressionUtility


class IndexPicker:
    @classmethod
    def update(self, results: ReferenceResults) -> bool:
        #
        # return true if a result was picked or indicated but
        # not found; otherwise, false.
        #
        ref = results.ref
        name = ref.name_one
        index = ExpressionUtility.to_int(name)
        if isinstance(index, int):
            if len(results.files) > index:
                results.files = [results.files[index]]
            else:
                results.files = []
            return True
        return False
