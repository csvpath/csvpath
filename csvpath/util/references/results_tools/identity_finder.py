import os
from csvpath.util.references.reference_results import ReferenceResults


class IdentityFinder:
    @classmethod
    def update(self, *, results: ReferenceResults) -> None:
        resolved = results.files[0] if results.files and len(results.files) else None
        if resolved is not None and results.ref.name_three is not None:
            resolved = os.path.join(resolved, results.ref.name_three)
            results.files[0] = resolved
