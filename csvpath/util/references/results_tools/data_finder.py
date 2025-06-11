import os
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.reference_exceptions import ReferenceException


class DataFinder:
    @classmethod
    def update(self, *, results: ReferenceResults) -> None:
        if len(results.ref.name_three_tokens) != 1:
            return
        if len(results.files) > 1:
            raise ReferenceException(
                "Cannot use data from more than one set of results"
            )
        resolved = results.files[0] if results.files and len(results.files) else None
        if resolved is not None:
            results.files = [
                os.path.join(resolved, f"{results.ref.name_three_tokens[0]}.csv")
            ]
