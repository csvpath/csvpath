from csvpath.util.references.reference_results import ReferenceResults


class FingerprintFinder:
    @classmethod
    def update(cls, results: ReferenceResults) -> None:
        if results.ref.name_one_is_fingerprint:
            n = results.ref.name_one
            mani = results.manifest
            for r in mani:
                if r.get("fingerprint") == n:
                    results.files.append(r.get("file"))
                    break
