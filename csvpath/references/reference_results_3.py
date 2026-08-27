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
    def __init__(
        self,
        *,
        path: str,
        uuid: str | None,
        data: Any = None,
        identity: str | None = None,
    ) -> None:
        if not path:
            raise ValueError("ReferenceResult3 path cannot be None or empty")
        if uuid is not None and not uuid:
            raise ValueError(
                "ReferenceResult3 uuid cannot be empty -- use None if there "
                "is no uuid (e.g. a directory-level, name_three-absent result "
                "has no single version/registration to identify)"
            )
        if identity is not None and not identity:
            raise ValueError(
                "ReferenceResult3 identity cannot be empty -- use None if "
                "there is none"
            )
        self._path = path
        self._uuid = uuid
        self._data = data
        self._identity = identity

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

    @property
    def identity(self) -> str | None:
        """which specific sub-entity, within path+uuid, this result is
        for -- added 2026-08-13 for CSVPATHS' statement-level range
        selector (":from()'/':to()"). Unlike FILES/RESULTS, CSVPATHS has
        no per-statement uuid at all (only the whole GROUP VERSION has
        one) -- path/uuid are identical across every statement matched
        by one query(), so _extract_data() cannot tell them apart from
        those two fields alone the way it can for the other two
        datatypes. None for every other case (path/uuid alone are
        already enough there)."""
        return self._identity

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, ReferenceResult3)
            and other.path == self._path
            and other.uuid == self._uuid
            and other.data == self._data
            and other.identity == self._identity
        )

    def __repr__(self) -> str:
        return (
            f"ReferenceResult3(path={self._path!r}, uuid={self._uuid!r}, "
            f"data={self._data!r}, identity={self._identity!r})"
        )


class ReferenceResults3:
    def __init__(
        self,
        *,
        results: list[ReferenceResult3] | None = None,
        ambiguous_content_read: bool = False,
    ) -> None:
        self._results = results or []
        #
        # set by a finder's own query() (2026-08-26, moved here alongside
        # the ":path()" retirement/Rule 1 relocation -- see reference_
        # finder_3.py's own resolve_from()) when query() found more than
        # one raw, unreduced candidate for a whole-resource content
        # accessor (:manifest(), :definition(), :errors(), etc.) with no
        # pointer to pick one -- Rule 1 (manifest_field_functions_
        # proposal.md's "Entity resolution and pooling" section) still
        # makes this illegal, but query() itself no longer raises for it;
        # only resolve()/resolve_from() does, once a caller actually
        # tries to read content rather than merely search. False for
        # every other query() result -- the common case.
        #
        self._ambiguous_content_read = ambiguous_content_read

    @property
    def results(self) -> list[ReferenceResult3]:
        return self._results

    @property
    def ambiguous_content_read(self) -> bool:
        return self._ambiguous_content_read

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
        """a new ReferenceResults3 holding only the entries whose path,
        uuid, or identity (added 2026-08-13, see ReferenceResult3.
        identity's own docstring for why) matches one of `identifiers`
        -- how resolve_from() turns a caller-narrowed list[str | UUID]
        back into a subset to resolve, without re-touching storage."""
        wanted = {str(i) for i in identifiers}
        selected = [
            r
            for r in self._results
            if r.path in wanted or r.uuid in wanted or r.identity in wanted
        ]
        return ReferenceResults3(
            results=selected, ambiguous_content_read=self._ambiguous_content_read
        )

    def deduplicated(self) -> "ReferenceResults3":
        """a new ReferenceResults3 with duplicate entries (by
        ReferenceResult3's own __eq__ -- path+uuid+data+identity)
        collapsed, first occurrence wins, order preserved -- added
        2026-08-17 for ReferenceExpression3's own UNION, which combines
        two datatypes' native results with no join-key logic at all
        (see references_notes/notes/reference_expressions_notes.txt's
        own ARCHITECTURE section: UNION never looks at a resolved field
        value, only at whether two results are already the same
        result). ReferenceResult3 has no __hash__ (defining __eq__
        without one already makes it unhashable, the correct default --
        see ReferenceResult3.data, a mutable field, which is exactly
        why), so this is a linear scan per entry, not a hash-set
        dedup -- fine at the result-set sizes this operates on."""
        seen: list = []
        for result in self._results:
            if result not in seen:
                seen.append(result)
        return ReferenceResults3(results=seen)

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
