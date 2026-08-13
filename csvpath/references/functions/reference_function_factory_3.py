from ..reference_3 import FunctionCall3
from ..reference_exceptions_3 import ReferenceException3
from .function_3 import Function3


class ReferenceFunctionFactory:
    #
    # name-keyed registry turning FunctionCall3 (parsed name+arg shape)
    # into real Function3 instances -- conceptually similar to
    # csvpath.matching.functions.function_factory.FunctionFactory, per
    # "requirements for functions.txt", but far smaller: references-v3
    # functions take at most 1 arg and have no argset overloads, so
    # there is no per-name construction complexity to speak of.
    #
    _FUNCTIONS: dict = {}

    @classmethod
    def _load(cls) -> None:
        from .selectors.all_3 import All3
        from .selectors.first_3 import First3
        from .selectors.flatten_3 import Flatten3
        from .selectors.from_3 import From3
        from .selectors.groups_3 import Groups3
        from .selectors.index_3 import Index3
        from .selectors.last_3 import Last3
        from .selectors.name_3 import Name3
        from .selectors.to_3 import To3

        from .well_known_files.data_3 import Data3
        from .well_known_files.definition_3 import Definition3
        from .well_known_files.errors_3 import Errors3
        from .well_known_files.file_3 import File3
        from .well_known_files.manifest_3 import Manifest3
        from .well_known_files.meta_3 import Meta3
        from .well_known_files.unmatched_3 import Unmatched3
        from .well_known_files.vars_3 import Vars3

        from .fields.actual_data_file_3 import ActualDataFile3
        from .fields.completed_3 import Completed3
        from .fields.destinations_3 import Destinations3
        from .fields.file_fingerprints_3 import FileFingerprints3
        from .fields.files_complete_3 import FilesComplete3
        from .fields.fingerprint_3 import Fingerprint3
        from .fields.home_3 import Home3
        from .fields.hostname_3 import Hostname3
        from .fields.identity_3 import Identity3
        from .fields.manifest_path_3 import ManifestPath3
        from .fields.mark_3 import Mark3
        from .fields.method_3 import Method3
        from .fields.named_file_home_3 import NamedFileHome3
        from .fields.named_file_name_3 import NamedFileName3
        from .fields.named_paths_count_3 import NamedPathsCount3
        from .fields.named_paths_identities_3 import NamedPathsIdentities3
        from .fields.named_paths_name_3 import NamedPathsName3
        from .fields.named_results_name_3 import NamedResultsName3
        from .fields.on_arrival_3 import OnArrival3
        from .fields.origin_3 import Origin3
        from .fields.origin_data_file_3 import OriginDataFile3
        from .fields.preceding_instance_identity_3 import (
            PrecedingInstanceIdentity3,
        )
        from .fields.run_uuid_3 import RunUuid3
        from .fields.scripts_3 import Scripts3
        from .fields.serial_3 import Serial3
        from .fields.source_mode_preceding_3 import SourceModePreceding3
        from .fields.sources_3 import Sources3
        from .fields.status_3 import Status3
        from .fields.time_3 import Time3
        from .fields.time_completed_3 import TimeCompleted3
        from .fields.transfers_3 import Transfers3
        from .fields.username_3 import Username3
        from .fields.uuid_3 import Uuid3
        from .fields.valid_3 import Valid3
        from .fields.webhooks_3 import Webhooks3

        from .filters.idchain_3 import Idchain3

        from .wrappers.path_3 import Path3

        cls._FUNCTIONS = {
            First3.NAME: First3,
            Last3.NAME: Last3,
            Index3.NAME: Index3,
            Name3.NAME: Name3,
            All3.NAME: All3,
            Flatten3.NAME: Flatten3,
            Groups3.NAME: Groups3,
            From3.NAME: From3,
            To3.NAME: To3,
            Manifest3.NAME: Manifest3,
            Definition3.NAME: Definition3,
            Errors3.NAME: Errors3,
            Vars3.NAME: Vars3,
            Meta3.NAME: Meta3,
            Data3.NAME: Data3,
            Unmatched3.NAME: Unmatched3,
            Idchain3.NAME: Idchain3,
            File3.NAME: File3,
            Uuid3.NAME: Uuid3,
            Time3.NAME: Time3,
            Fingerprint3.NAME: Fingerprint3,
            Home3.NAME: Home3,
            Origin3.NAME: Origin3,
            Mark3.NAME: Mark3,
            NamedPathsIdentities3.NAME: NamedPathsIdentities3,
            NamedPathsCount3.NAME: NamedPathsCount3,
            OnArrival3.NAME: OnArrival3,
            Sources3.NAME: Sources3,
            Scripts3.NAME: Scripts3,
            Webhooks3.NAME: Webhooks3,
            Transfers3.NAME: Transfers3,
            Destinations3.NAME: Destinations3,
            Path3.NAME: Path3,
            RunUuid3.NAME: RunUuid3,
            Serial3.NAME: Serial3,
            Valid3.NAME: Valid3,
            Completed3.NAME: Completed3,
            FilesComplete3.NAME: FilesComplete3,
            NamedFileName3.NAME: NamedFileName3,
            NamedFileHome3.NAME: NamedFileHome3,
            NamedResultsName3.NAME: NamedResultsName3,
            NamedPathsName3.NAME: NamedPathsName3,
            Status3.NAME: Status3,
            Method3.NAME: Method3,
            Hostname3.NAME: Hostname3,
            Username3.NAME: Username3,
            TimeCompleted3.NAME: TimeCompleted3,
            ManifestPath3.NAME: ManifestPath3,
            Identity3.NAME: Identity3,
            ActualDataFile3.NAME: ActualDataFile3,
            OriginDataFile3.NAME: OriginDataFile3,
            FileFingerprints3.NAME: FileFingerprints3,
            SourceModePreceding3.NAME: SourceModePreceding3,
            PrecedingInstanceIdentity3.NAME: PrecedingInstanceIdentity3,
        }

    @classmethod
    def add_function(cls, function_cls: type) -> None:
        """registers a function class at runtime -- e.g. for a custom,
        user-added function (see "requirements for functions.txt"'s
        possible-requirements section). overrides an existing name."""
        if function_cls is None:
            raise ValueError("function_cls cannot be None")
        if not cls._FUNCTIONS:
            cls._load()
        cls._FUNCTIONS[function_cls.NAME] = function_cls

    @classmethod
    def get_registered_class(cls, name: str) -> type | None:
        """the registered Function3 CLASS for `name`, or None if
        unknown -- for checking class-level metadata (e.g. ROLE)
        without constructing/validating an instance. Used by
        InterpolatedString3.check_valid() to reject non-VALUE
        functions inside a "{...}" interpolation without needing to
        evaluate them."""
        if not cls._FUNCTIONS:
            cls._load()
        return cls._FUNCTIONS.get(name)

    @classmethod
    def build(cls, call: FunctionCall3) -> Function3:
        """compiles one FunctionCall3 into a real, validated Function3.
        recurses first if call.arg is itself a FunctionCall3, so a
        nested function is always compiled (and check_valid()'d) before
        the function that takes it as an argument."""
        if call is None:
            raise ValueError("FunctionCall3 cannot be None")
        if not cls._FUNCTIONS:
            cls._load()
        arg = call.arg
        if isinstance(arg, FunctionCall3):
            arg = cls.build(arg)
        function_cls = cls._FUNCTIONS.get(call.name)
        if function_cls is None:
            raise ReferenceException3(f"Unknown reference function: {call.name}")
        instance = function_cls(arg=arg)
        instance.check_valid()
        return instance

    @classmethod
    def build_chain(cls, calls: list) -> list:
        """compiles a whole function chain (NameOne3/NameThree3's
        .functions list) and enforces "at most one pointer function per
        chain, per nesting level" -- see "requirements for
        functions.txt". a pointer nested inside another function's
        argument (already compiled by build() above) does not count
        here; only these direct siblings do."""
        built = [cls.build(call) for call in calls]
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        if len(pointers) > 1:
            names = ", ".join(f":{f.name}()" for f in pointers)
            raise ReferenceException3(
                f"At most one pointer function is allowed per function chain, "
                f"found {len(pointers)}: {names}"
            )
        return built
