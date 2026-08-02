from typing import Any
from uuid import UUID


#
# ReferenceResult3/ReferenceResults3 are pure value containers -- a
# path+uuid (+ optionally data, once resolved) and a list of the same.
# deliberately not modeled on v2's ReferenceResults, which holds ref and
# csvpaths and does its own filesystem/manifest lookups (.manifest,
# .runs_manifest_path) -- that mixes "holds the output" with "knows how
# to reach storage." here, only ReferenceFinder3 (and its concrete
# per-datatype subclasses) ever talks to storage; these two classes just
# hold what was found.
#


class ReferenceResult3:
    def __init__(self, *, path: str, uuid: str | None, data: Any = None) -> None:
        if not path:
            raise ValueError("ReferenceResult3 path cannot be None or empty")
        if uuid is not None and not uuid:
            raise ValueError(
                "ReferenceResult3 uuid cannot be empty -- use None if there "
                "is no uuid (e.g. a directory-level, name_three-absent result "
                "has no single version/registration to identify)"
            )
        self._path = path
        self._uuid = uuid
        self._data = data

    @property
    def path(self) -> str:
        return self._path

    @property
    def uuid(self) -> str | None:
        return self._uuid

    @property
    def data(self) -> Any:
        return self._data

    @data.setter
    def data(self, data: Any) -> None:
        # the only mutable field -- query() finds path+uuid, resolve()
        # fills data in afterward on the same instances.
        self._data = data

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, ReferenceResult3)
            and other.path == self._path
            and other.uuid == self._uuid
            and other.data == self._data
        )

    def __repr__(self) -> str:
        return (
            f"ReferenceResult3(path={self._path!r}, uuid={self._uuid!r}, "
            f"data={self._data!r})"
        )


class ReferenceResults3:
    def __init__(self, *, results: list[ReferenceResult3] | None = None) -> None:
        self._results = results or []

    @property
    def results(self) -> list[ReferenceResult3]:
        return self._results

    @property
    def files(self) -> list[str]:
        return [r.path for r in self._results]

    @property
    def uuids(self) -> list[str | None]:
        return [r.uuid for r in self._results]

    def file_for_uuid(self, uuid: str | UUID) -> str | None:
        uuid = str(uuid)
        for r in self._results:
            if r.uuid == uuid:
                return r.path
        return None

    def uuid_for_file(self, file: str) -> str | None:
        for r in self._results:
            if r.path == file:
                return r.uuid
        return None

    def data_for_uuid(self, uuid: str | UUID) -> Any:
        uuid = str(uuid)
        for r in self._results:
            if r.uuid == uuid:
                return r.data
        return None

    def select(self, identifiers: list) -> "ReferenceResults3":
        """a new ReferenceResults3 holding only the entries whose path
        or uuid matches one of `identifiers` -- how resolve_from() turns
        a caller-narrowed list[str | UUID] back into a subset to
        resolve, without re-touching storage."""
        wanted = {str(i) for i in identifiers}
        selected = [r for r in self._results if r.path in wanted or r.uuid in wanted]
        return ReferenceResults3(results=selected)

    def remove(self, result: ReferenceResult3) -> None:
        """drops one result in place -- for the "iterate, decide, trim"
        workflow: walk the results, remove the ones you do not want,
        then hand what is left straight to a finder's resolve_from().
        raises ValueError if result is not present (same as
        list.remove()). safe to call from inside a `for r in results:`
        loop -- see __iter__."""
        self._results.remove(result)

    def __len__(self) -> int:
        return len(self._results)

    def __iter__(self):
        # a snapshot, not the live list: iterating and calling remove()
        # on the same result within one loop must not skip entries the
        # way iterating-while-mutating a list normally would.
        return iter(list(self._results))

    def __eq__(self, other) -> bool:
        return isinstance(other, ReferenceResults3) and other.results == self._results

    def __repr__(self) -> str:
        return f"ReferenceResults3(results={self._results!r})"
