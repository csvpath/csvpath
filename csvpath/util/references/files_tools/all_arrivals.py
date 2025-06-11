from csvpath.util.references.reference_results import ReferenceResults


class AllArrivals:

    #
    # if we have no name_one we are looking for everything that has arrived.
    #
    @classmethod
    def update(cls, results: ReferenceResults) -> None:
        if results.ref.name_one is not None:
            return
        results.files = [_["file"] for _ in results.manifest]
