from csvpath.util.references.reference_results import ReferenceResults


class ManifestOrder:
    @classmethod
    def update(cls, results: ReferenceResults) -> None:
        if len(results.files) == 0:
            return
        files = results.files
        ordered = [_["file"] for _ in results.manifest if _["file"] in files]
        results.files = ordered
