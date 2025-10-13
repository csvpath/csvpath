import os
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.nos import Nos


class IdentityFinder:
    @classmethod
    def update(self, *, results: ReferenceResults) -> None:
        resolved = (
            results.files[0] if results.files and len(results.files) == 1 else None
        )
        if resolved is not None and results.ref.name_three is not None:
            _ = resolved
            resolved = Nos(resolved).join(results.ref.name_three)
            nos = Nos(resolved)
            #
            # not clear exists() is every really the right call, but it definitely is not for the
            # cloud backends where the concept of a directory is sketchy. but it was here so leaving
            # it, in addition to dir_exists.
            #
            if nos.exists() or nos.dir_exists():
                results.files[0] = resolved
            else:
                results.files = []
