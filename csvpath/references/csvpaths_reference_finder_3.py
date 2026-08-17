from csvpath.util.nos import Nos

from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Reference3, Star3
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_3 import ReferenceFinder3
from .reference_results_3 import ReferenceResult3, ReferenceResults3


class CsvpathsReferenceFinder3(ReferenceFinder3):
    #
    # first pass, deliberately narrow, mirroring FilesReferenceFinder3's
    # scoping approach -- but note the roles of name_one/name_three are
    # REVERSED from files here:
    #  - root_major is a literal named-paths group name, or "*" (every
    #    group). "*" has two exceptions carved out before general
    #    traversal (Rule 1a/1b, a bare/ordinal-indexed :manifest() reads
    #    the global loads ledger); any other use of "*" goes through
    #    _query_star_traversal(), which generalizes name_one's own
    #    version-selecting chain across every group -- see that
    #    method's docstring for the flatten-vs-group distinction and
    #    its own narrower scope.
    #  - name_one IS the version selector for csvpaths (STRUCTURE table:
    #    "name_one is always one or more versions of a named-paths
    #    group's group.csvpaths file"). Its combined function chain
    #    (the sole path-segment function plus any trailing chain) may
    #    contain at most one pointer function (:first()/:last()/
    #    :index(n)): if present, it reduces to that one version; if
    #    absent (e.g. a bare :all()), every version in the manifest is
    #    returned, unreduced -- this is how "list of versions in the
    #    form: (path-to-group.csvpaths, uuid)" (STRUCTURE table) is
    #    actually reached. ":having('identity')' (added 2026-08-13)
    #    filters the version list down to versions whose own
    #    named_paths_identities actually contains that identity, before
    #    any pointer reduces further. ":from()'/':to()' (also added
    #    2026-08-13, David: a named-paths group's own load time is a
    #    real arrival-date concept, "give me the versions loaded between
    #    date-one and date-two") then windows the (possibly ':having()'-
    #    filtered) version list to a RANGE, before any pointer reduces
    #    that -- index-mode (int/:index(n)) POSITIONALLY slices;
    #    date-mode (str/:date(...)) FILTERS by each version's own "time"
    #    manifest field (see functions/fields/time_3.py). Mixing modes
    #    in one pair is rejected. Not yet supported combined with '*'
    #    traversal -- see _resolve_versions/_query_star_traversal.
    #    ":manifest()" may ride alongside the version
    #    pointer in this same combined chain (e.g. ":last():manifest()")
    #    -- it never narrows/selects itself (see functions/manifest_3.py),
    #    it just changes what _extract_data() resolves to: the matched
    #    version's own manifest entry, instead of its statement text.
    #    Literal/"*"/path-building content, and the
    #    "#worksheet" marker (name_two, files-only), are not meaningful
    #    for csvpaths and are rejected. :uuid() is not yet a registered
    #    function, so it is "not yet supported" for now like any other
    #    unbuilt function.
    #  - name_three, if present, is either a literal identity lookup
    #    into that version's named_paths_identities list -- matched by
    #    identity string, or by the stringified index an unnamed
    #    statement is given at load time (both already live in
    #    named_paths_identities, so a single exact-match lookup covers
    #    both cases) -- OR ":from()'/':to()' (added 2026-08-13),
    #    windowing that same ordered identities list to a positional
    #    range (index-mode only -- unlike name_one's own ':from()'/
    #    ':to()' above, an individual STATEMENT has no arrival time of
    #    its own, only the GROUP VERSION it belongs to does, so date-
    #    mode bounds are rejected here specifically). A literal identity
    #    and a range are mutually exclusive on the same name_three. Because
    #    csvpaths has no per-statement uuid (only the whole GROUP
    #    VERSION has one), a range's results share identical path/uuid
    #    across every matched statement -- ReferenceResult3.identity
    #    (see its own docstring) is what _extract_data() uses to tell
    #    them apart. No other function chain on name_three is supported
    #    yet (see "creating references v3.txt"'s † footnote on this).
    #
    # storage facts this relies on (confirmed against PathsManager/
    # PathsRegistrar and the real per-group manifest schema, not
    # assumed): a named-paths group's manifest.json is one flat,
    # append-only JSON array, one entry per loaded/reloaded version of
    # the WHOLE group -- there is only one group.csvpath file, always
    # the same path, regardless of version. Each entry's "named_paths"
    # is a list of that version's individual csvpath statement source
    # strings, and "named_paths_identities" is a parallel list of each
    # statement's name/id (or its stringified load-time index, if
    # unnamed). Arrival order is simply array order.
    #

    def query(self) -> ReferenceResults3:
        reference = self.ref.parsed
        root_major = reference.root_major
        if isinstance(root_major, Star3):
            if self._is_bare_pointer_reference(reference, "manifest"):
                # Rule 1a (manifest_field_functions_proposal.md): "*" at
                # root_major combined with a bare :manifest() is the one
                # exception -- it resolves to the Named-Paths Loads
                # Manifest, a single global ledger at the named-paths
                # root tracking every load across every named-paths
                # group (see paths_listener.py). :definition() has no
                # equivalent global resource, so it stays unsupported
                # here, same as any other function.
                home = self.csvpaths.config.inputs_csvpaths_path
                return self._query_well_known_file(home, "manifest.json")
            pointer_call = self._pointer_before_manifest(reference, "manifest")
            if pointer_call is not None:
                # Rule 1b -- a pointer riding before the bare :manifest()
                # (e.g. "$*.csvpaths.:last():manifest()") selects one
                # entry out of the global ledger by ordinal position,
                # instead of dumping the whole thing.
                home = self.csvpaths.config.inputs_csvpaths_path
                path = Nos(home).join("manifest.json")
                ledger = self.csvpaths.paths_manager.paths_root_manifest
                selected = self._apply_pointer(pointer_call, ledger)
                if selected is None:
                    return ReferenceResults3(results=[])
                return ReferenceResults3(
                    results=[ReferenceResult3(path=path, uuid=selected["uuid"])]
                )
            return self._query_star_traversal(reference)

        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) -- it is files-only."
            )

        if self._is_bare_pointer_reference(
            reference, "manifest"
        ) or self._is_bare_pointer_reference(reference, "definition"):
            # both ":manifest()" and ":definition()" are a bare, sole-
            # content name_one whose function name IS the JSON file's
            # own name (manifest.json/definition.json) -- see
            # _query_well_known_file() on the ABC.
            home = self.csvpaths.paths_manager.named_paths_home(root_major)
            filename = f"{name_one.path[0].name}.json"
            return self._query_well_known_file(home, filename)

        manifest = self.csvpaths.paths_manager.get_manifest_for_name(root_major)
        selected_versions = self._resolve_versions(name_one, manifest)

        if len(selected_versions) > 1:
            combined = [
                seg
                for seg in (name_one.path[0], *name_one.functions)
                if isinstance(seg, FunctionCall3)
            ]
            # checked by direct name, not contains_function_named's
            # recursive search -- :manifest() is never itself nested
            # inside another function's arg except :path()'s (e.g.
            # :path(:manifest())), which is deliberately exempt from
            # this rule (Rule 2, poolable). A recursive check would
            # incorrectly flag that case too.
            has_manifest = any(seg.name == "manifest" for seg in combined)
            if has_manifest:
                # Resolving full manifest content always touches exactly
                # one entity (settled 2026-08-07, see manifest_field_
                # functions_proposal.md's "Entity resolution and pooling"
                # section) -- more than one version here needs a pointer
                # to pick which one.
                raise ReferenceException3(
                    "CsvpathsReferenceFinder3 requires a pointer (:first()/"
                    ":last()/:index(n)) to pick one version when combining "
                    ":manifest() with no pointer matches more than one "
                    "version -- resolving full manifest content always "
                    "touches exactly one entity."
                )

        name_three = reference.name_three
        from_call = to_call = None
        if name_three is not None:
            if name_three.functions:
                built = ReferenceFunctionFactory.build_chain(name_three.functions)
                # replaces a hand-written "unrecognized" check (settled
                # 2026-08-14) -- see _check_position()'s own docstring
                # and _resolve_versions()'s equivalent check for
                # name_one. Only :from()/:to() declare name_three as
                # legal for csvpaths, so this rejects anything else
                # (e.g. a literal identity's own function chain trying
                # to add something other than a range) exactly as
                # before, just via the shared mechanism instead of a
                # local tuple.
                for f in built:
                    self._check_position(f, Reference3.NAME_THREE, Reference3.CSVPATHS)
                from_call = next((f for f in built if f.name == "from"), None)
                to_call = next((f for f in built if f.name == "to"), None)
                for f in (from_call, to_call):
                    if f is not None and isinstance(self._range_bound(f), str):
                        raise ReferenceException3(
                            "CsvpathsReferenceFinder3's ':from()'/':to()' "
                            "only supports index-mode bounds (int/:index(n)) "
                            "-- statements have no arrival date of their own."
                        )
                if name_three.body is not None and (from_call or to_call):
                    raise ReferenceException3(
                        "CsvpathsReferenceFinder3 cannot combine a literal "
                        "identity with ':from()'/':to()' -- they select "
                        "statements two different, contradictory ways."
                    )
            if (
                name_three.body is None
                and from_call is None
                and to_call is None
            ) or isinstance(name_three.body, Star3):
                raise ReferenceException3(
                    "CsvpathsReferenceFinder3 requires name_three to be a "
                    "literal statement identity/index, or ':from()'/':to()'."
                )

        results = []
        for selected in selected_versions:
            if name_three is None:
                results.append(
                    ReferenceResult3(
                        path=selected["group_file_path"], uuid=selected["uuid"]
                    )
                )
                continue
            identities = selected.get("named_paths_identities") or []
            if from_call is not None or to_call is not None:
                # ':from()'/':to()' as a name_three statement range --
                # added 2026-08-13, David's own FlightPath v2 use case:
                # rewind/replay starting from a specific csvpath
                # statement (e.g. "$acme.csvpaths.:last().:from(:index(2))").
                # Windows THIS version's own ordered statement-identity
                # list, one ReferenceResult3 per identity in the window
                # -- each carries its OWN identity (see
                # ReferenceResult3.identity's docstring for why this is
                # necessary: path/uuid are identical across every
                # statement in ONE version, CSVPATHS has no per-
                # statement uuid at all).
                windowed = self._apply_range(identities, from_call, to_call)
                for identity in windowed:
                    results.append(
                        ReferenceResult3(
                            path=selected["group_file_path"],
                            uuid=selected["uuid"],
                            identity=identity,
                        )
                    )
            else:
                if self._find_by_identity(name_three.body, identities) is None:
                    continue
                results.append(
                    ReferenceResult3(
                        path=selected["group_file_path"],
                        uuid=selected["uuid"],
                        identity=name_three.body,
                    )
                )
        return ReferenceResults3(results=results)

    def _query_star_traversal(self, reference: Reference3) -> ReferenceResults3:
        """root_major == "*" -- query across every named-paths group,
        not just one. Unlike FILES, csvpaths' version-selecting pointer
        and ':all()' both already live in name_one's own combined chain
        (see _resolve_versions) -- there is no separate name_three
        pointer slot to borrow the way FILES uses. Two semantics, each
        generalizing this datatype's own existing single-group
        precedent rather than copying FILES' shape verbatim:

        - bare pointer, no ':all()' (FLATTEN): every named-paths
          group's whole manifest pools into one combined list, sorted
          by each entry's own "time" so the pointer means true
          chronological order across everything, not enumeration order
          (csvpaths has no path dimension the way files does, so there
          is nothing to pattern-match -- every entry in every group's
          manifest is a candidate).
        - ':all()' present in the combined chain (GROUP): the pointer
          is applied independently within each group's own manifest
          (plain array order -- no time-sort needed within one group)
          -- one result per group. With ':all()' and no pointer, this
          extends csvpaths' own existing single-group precedent
          (_resolve_versions: no pointer means every version,
          unreduced) across every group instead of deduping to
          anything -- there is no path dimension to dedupe to, unlike
          FILES.

        Deliberately narrow, matching FILES' own scoping: combining '*'
        traversal with :manifest(), name_three, is not yet supported --
        raises clearly rather than guessing. A registered field-accessor
        function (e.g. :uuid(), :named_paths_name()) IS now supported
        alongside the pointer (added 2026-08-18, mirroring RESULTS' own
        equivalent fix) -- _extract_data() resolves it via
        _group_manifest_entry(), which searches every group's manifest
        for the matched uuid when root_major is the '*' token, instead
        of the direct get_manifest_for_name(reference.root_major) call
        every non-star call site uses (that direct call is what broke
        for '*' before this fix -- no group is actually named "*").
        """
        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) -- it is files-only."
            )
        if reference.name_three is not None:
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 does not yet support name_three "
                "(a statement identity lookup) combined with '*' traversal."
            )
        if len(name_one.path) != 1 or not isinstance(name_one.path[0], FunctionCall3):
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 requires name_one to be a version-"
                "selecting function chain (e.g. :last(), :all()) when "
                "traversing every named-paths group with '*'."
            )
        # a plain pointer + :manifest() (e.g. ":last():manifest()") never
        # reaches this method at all -- query()'s own _pointer_before_
        # manifest() check above already claims that exact shape as
        # Rule 1b (the global-ledger ordinal case). Only a manifest
        # combined with ':all()' (not a pointer-first shape) or a
        # 3+-function chain reaches the guard below.
        calls = [name_one.path[0], *name_one.functions]
        built = ReferenceFunctionFactory.build_chain(calls)
        is_grouped = any(f.name == "all" for f in built)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        unsupported = any(f.name == "manifest" for f in built) or any(
            f.name in ("from", "to") for f in built
        )
        if unsupported:
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 does not yet support combining "
                "'*' traversal with :manifest() or ':from()'/':to()' -- "
                "only a plain pointer (:first()/:last()/:index(n)), "
                "optionally combined with :all() for one result per "
                "group, or a registered field-accessor function (e.g. "
                ":uuid()), is supported so far."
            )

        if is_grouped:
            selected_versions = []
            for name in self.csvpaths.paths_manager.named_paths_names:
                manifest = self.csvpaths.paths_manager.get_manifest_for_name(name)
                if pointers:
                    selected = self._apply_pointer(pointers[0], manifest)
                    if selected is not None:
                        selected_versions.append(selected)
                else:
                    selected_versions.extend(manifest)
        else:
            if not pointers:
                raise ReferenceException3(
                    "CsvpathsReferenceFinder3 requires a pointer (:first()/"
                    ":last()/:index(n)) when traversing every named-paths "
                    "group with '*' -- use :all() for one result per "
                    "group instead."
                )
            pooled = []
            for name in self.csvpaths.paths_manager.named_paths_names:
                pooled.extend(
                    self.csvpaths.paths_manager.get_manifest_for_name(name)
                )
            pooled.sort(key=lambda e: e["time"])
            selected = self._apply_pointer(pointers[0], pooled)
            selected_versions = [selected] if selected is not None else []

        return ReferenceResults3(
            results=[
                ReferenceResult3(path=c["group_file_path"], uuid=c["uuid"])
                for c in selected_versions
            ]
        )

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        # :path(...) is checked before resolve_kind's content-oriented
        # dispatch -- see FilesReferenceFinder3._extract_data() for why.
        name_one = reference.name_one
        combined_for_path = [
            seg
            for seg in (name_one.path[0], *name_one.functions)
            if isinstance(seg, FunctionCall3)
        ]
        path_call = self._find_path_call(combined_for_path)
        if path_call is not None:
            home = self.csvpaths.paths_manager.named_paths_home(
                reference.root_major
            )
            return self._resolve_path_call(path_call, home)
        kind = reference.resolve_kind
        if kind == Reference3.METADATA_FILE:
            if self._is_bare_pointer_reference(
                reference, "manifest"
            ) or self._is_bare_pointer_reference(reference, "definition"):
                # result.path is already the manifest.json/definition.json
                # path itself (set by query()'s _query_well_known_file()
                # branch above).
                return self._read_well_known_file(result.path)
            if isinstance(reference.root_major, Star3) and result.uuid is not None:
                # Rule 1b -- a pointer already reduced the global ledger
                # to one entry in query(); re-derive it the same way the
                # per-group branch below does, just against the ledger
                # instead of a named-paths groups own manifest.
                ledger = self.csvpaths.paths_manager.paths_root_manifest
                return self._find_manifest_entry_by_uuid(ledger, result.uuid)
            name_one = reference.name_one
            has_manifest = any(
                seg.contains_function_named("manifest")
                for seg in (name_one.path[0], *name_one.functions)
                if isinstance(seg, FunctionCall3)
            )
            if has_manifest:
                # :manifest() riding alongside the real version-selecting
                # pointer already in name_one's own combined chain (e.g.
                # ":last():manifest()") -- give the matched version's own
                # manifest entry, not the whole raw file. root_major is
                # never the '*' token here -- Rule 1b above already
                # claims the star + bare-pointer-plus-manifest shape, and
                # _query_star_traversal itself still rejects ':manifest()'
                # combined with '*' traversal -- but routed through
                # _group_manifest_entry() anyway for consistency with the
                # field-accessor branch below, which genuinely does need
                # to handle root_major being '*'.
                _, entry = self._group_manifest_entry(
                    reference.root_major, result.uuid
                )
                return entry
        if kind == Reference3.METADATA_FIELD:
            # a registered field-accessor function (e.g. :uuid()) in the
            # same combined chain :manifest() itself rides in -- extracts
            # one key from the matched version's manifest entry (or, for
            # a definition.json-backed field, the group's definition
            # config) instead of the whole entry.
            field_call = self._find_field_function_call(combined_for_path)
            if field_call is not None:
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    field_call.name
                )
                key_path = function_cls.KEY.get(reference.datatype)
                if function_cls.SOURCE == "definition":
                    # a definition.json-backed field (e.g. :scripts(),
                    # :webhooks()) is keyed by group NAME, not uuid --
                    # _group_manifest_entry() re-derives which real group
                    # this is even when root_major is the '*' token
                    # (added 2026-08-18, see that method's own docstring).
                    group_name, _ = self._group_manifest_entry(
                        reference.root_major, result.uuid
                    )
                    config = self.csvpaths.paths_manager.describer.get_config(
                        group_name
                    )
                    entry = config.model_dump(exclude_none=True)
                else:
                    _, entry = self._group_manifest_entry(
                        reference.root_major, result.uuid
                    )
                return self._extract_field_value(entry, key_path)
        if kind != Reference3.FIRST_PARTY:
            raise ReferenceException3(
                f"CsvpathsReferenceFinder3 does not yet support "
                f"resolve_kind={kind!r} -- only :manifest()/:definition() "
                "and registered field-accessor functions are wired up as "
                "metadata-file/field functions so far."
            )
        name_three = reference.name_three
        if name_three is None:
            # a whole group version has no single unambiguous payload --
            # the same "no default" rule as a directory-level, name_one-
            # terminal result in FilesReferenceFinder3.
            return None
        if result.identity is None:
            # should not happen once every name_three-bearing result
            # carries its own identity (query() sets it unconditionally
            # now, both for the literal-identity case and the
            # ':from()'/':to()' range case, added 2026-08-13) -- guarded
            # defensively rather than assumed.
            return None

        manifest = self.csvpaths.paths_manager.get_manifest_for_name(
            reference.root_major
        )
        selected = self._find_manifest_entry_by_uuid(manifest, result.uuid)
        if selected is None:
            return None
        identities = selected.get("named_paths_identities") or []
        # uses result.identity, NOT name_three.body -- settled 2026-08-13:
        # a ':from()'/':to()' range produces several results sharing one
        # version's path/uuid, each identified only by its OWN identity
        # (see ReferenceResult3.identity's docstring). name_three.body is
        # only ever set for the single-literal-identity shape, so it
        # cannot distinguish results in a range the way result.identity
        # already does for every shape.
        index = self._find_by_identity(result.identity, identities)
        if index is None:
            return None
        statements = selected.get("named_paths") or []
        return statements[index]

    def _group_manifest_entry(self, root_major, uuid: str) -> tuple:
        """returns (group_name, manifest_entry) for the version matching
        uuid. When root_major is the '*' token (a '*' traversal result --
        added 2026-08-18) the matched version could belong to any named-
        paths group, so every group's own manifest is searched for the
        matching uuid -- uuids are assumed globally unique, the same
        assumption _find_manifest_entry_by_uuid's every other call site
        already makes. Otherwise root_major is a literal group name --
        looked up directly, same as every call site used to do inline
        before this helper existed. Acceptable performance-wise since a
        csvpaths install typically has few named-paths groups, unlike
        RESULTS' potentially-large run history (RESULTS did not need an
        equivalent helper for this same reason -- see
        ResultsReferenceFinder3._extract_data's own comment on why)."""
        if isinstance(root_major, Star3):
            for name in self.csvpaths.paths_manager.named_paths_names:
                manifest = self.csvpaths.paths_manager.get_manifest_for_name(name)
                entry = self._find_manifest_entry_by_uuid(manifest, uuid)
                if entry is not None:
                    return name, entry
            return None, None
        manifest = self.csvpaths.paths_manager.get_manifest_for_name(root_major)
        return root_major, self._find_manifest_entry_by_uuid(manifest, uuid)

    def _resolve_versions(self, name_one, manifest: list) -> list:
        """name_one's sole job for csvpaths is selecting which
        version(s) to work with, so its path_prefix must reduce to
        exactly one function-segment (no literal/"*" path-building, no
        worksheet marker) -- combined with its own trailing function
        chain, if any. Every function in that combined chain must
        declare name_one as legal for csvpaths in its own POSITIONS
        (added 2026-08-14, see ReferenceFinder3._check_position()) --
        e.g. ":name()" is registered for csvpaths but has nowhere legal
        to go there, so it now raises here instead of silently no-
        opping the way it used to. ':having("identity")' (added
        2026-08-13) filters
        `manifest` down to versions whose own "named_paths_identities"
        list contains that identity, BEFORE any pointer reduces further
        -- e.g. ":having('my_validations'):last()" is "the last version
        that actually has a my_validations statement." ':from()'/':to()'
        (added 2026-08-13, David: a named-paths group's own load time is
        a real arrival-date concept -- "give me the versions loaded
        between date-one and date-two") window the (possibly
        ':having()'-filtered) manifest to a RANGE next, same position
        RESULTS'/FILES' own version-level range occupies -- index-mode
        (int/:index(n)) POSITIONALLY slices via the shared
        _apply_range(); date-mode (str/:date(...)) FILTERS by each
        version's own "time" manifest field via the shared
        _apply_manifest_date_range(). At most one pointer function is
        allowed among the combined chain (build_chain() enforces this):
        if present, it reduces the (possibly filtered/windowed) list to
        that one version -- riding alongside ':from()'/':to()', it
        reduces the RANGE, not the full candidate set, same as FILES.
        If absent (e.g. a bare :all()), every version in the list is
        returned, unreduced."""
        if len(name_one.path) != 1 or not isinstance(name_one.path[0], FunctionCall3):
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 requires name_one to be a version-"
                "selecting function chain (e.g. :last(), :all()) -- "
                "literal/'*' path-building is not meaningful for csvpaths."
            )
        calls = [name_one.path[0], *name_one.functions]
        built = ReferenceFunctionFactory.build_chain(calls)
        for f in built:
            self._check_position(f, Reference3.NAME_ONE, Reference3.CSVPATHS)
        having_call = next((f for f in built if f.name == "having"), None)
        if having_call is not None:
            manifest = [
                entry
                for entry in manifest
                if having_call.arg in (entry.get("named_paths_identities") or [])
            ]
        from_call = next((f for f in built if f.name == "from"), None)
        to_call = next((f for f in built if f.name == "to"), None)
        if from_call is not None or to_call is not None:
            from_bound = self._range_bound(from_call) if from_call is not None else None
            to_bound = self._range_bound(to_call) if to_call is not None else None
            from_is_date = isinstance(from_bound, str)
            to_is_date = isinstance(to_bound, str)
            if (from_bound is not None and to_bound is not None) and (
                from_is_date != to_is_date
            ):
                # rejected -- not because it is meaningless (e.g.
                # ":from(:date('2025-01-01')):to(:index(10))" is a
                # reasonable ask: "10 versions starting from this
                # date"), but because it is AMBIGUOUS and undecided
                # which of at least two readings is meant -- is the
                # index bound absolute position in the full version
                # list, or relative to wherever the date bound starts
                # matching? Nothing here picks one, so mixing is
                # rejected until that anchor semantics question is
                # deliberately settled, not attempted here for lack of
                # a driving use case (same reasoning as RESULTS'/FILES'
                # own version-level ranges).
                raise ReferenceException3(
                    "CsvpathsReferenceFinder3 does not support mixing "
                    "index-mode and date-mode ':from()'/':to()' bounds in "
                    "the same range."
                )
            if from_is_date or to_is_date:
                if from_is_date:
                    self._validate_date_format(from_bound)
                if to_is_date:
                    self._validate_date_format(to_bound)
                manifest = self._apply_manifest_date_range(
                    manifest, from_bound, to_bound
                )
            else:
                manifest = self._apply_range(manifest, from_call, to_call)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        if not pointers:
            return manifest
        selected = self._apply_pointer(pointers[0], manifest)
        return [selected] if selected is not None else []
