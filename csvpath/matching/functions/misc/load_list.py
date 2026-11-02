# pylint: disable=C0114
from csvpath.matching.productions import Term
from csvpath.matching.util.exceptions import MatchException
from csvpath.managers.paths.paths_asset_manager import PathsAssetManager
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from ..function_focus import ValueProducer
from ..args import Args


class LoadList(ValueProducer):
    """loads a value-per-line text list, once, as a list value"""

    def check_valid(self) -> None:
        #
        # listed so the generated docs show it: lists can be large, and tmp
        # keeps them out of vars.json
        #
        self.value_qualifiers.append("tmp")
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Loads a list of values, one per line, from a text file. The
                value is a list (a tuple, which cannot be changed) that in()
                and other functions can use, e.g.:

                @ids.tmp = load_list("ids")
                in( #id, @ids )

                In a named-paths group run the argument is the list's name,
                and the list is the group's assets/<name>.txt. Lists are
                stored with the paths manager's asset manager store_list().
                Outside a group run the argument is the path of a .txt
                file.

                Blank lines are skipped and each value is stripped of
                surrounding whitespace. The list is loaded once, when the
                csvpath is validated; a list that cannot be loaded is an
                error then, before any line is read. Use the tmp qualifier
                to keep a large list out of vars.json.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(1).arg(name="list name or path", types=[Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()
        self._values = self._load()

    def _load(self) -> tuple[str, ...]:
        csvpath = self.matcher.csvpath
        arg = self._value_one()
        try:
            path = self._path(arg=arg)
            if not Nos(path).exists():
                raise ValueError(f"No list at {path}")
            with DataFileReader(path=path) as reader:
                text = reader.read()
        except Exception as e:  # pylint: disable=W0718
            msg = f"Cannot load list {arg!r}: {e}"
            csvpath.logger.exception(msg)
            csvpath.error_manager.handle_error(source=self, msg=msg)
            #
            # a csvpath that can't load its list must not look like a
            # clean run, even when errors don't raise
            #
            csvpath.is_valid = False
            raise MatchException(msg) from e
        values = []
        for line in f"{text}".splitlines():
            v = line.strip()
            if v != "":
                values.append(v)
        #
        # a tuple: every line gets the same list, so it must not be
        # changeable
        #
        return tuple(values)

    def _path(self, *, arg) -> str:
        if not isinstance(arg, str) or arg.strip() == "":
            raise ValueError("load_list() needs a list name or a .txt path")
        csvpath = self.matcher.csvpath
        group = csvpath.named_paths_name
        if csvpath.csvpaths is not None and group is not None:
            #
            # a group run: the list must be the group's. no fallback to a
            # file path, so a run never loads a list from somewhere else
            #
            return csvpath.csvpaths.paths_manager.asset_manager.list_path(
                name=group, list_name=arg
            )
        if not arg.endswith(PathsAssetManager.LIST_SUFFIX):
            raise ValueError(
                f"Outside a named-paths group run, load_list() needs the path of a "
                f"{PathsAssetManager.LIST_SUFFIX} file, not {arg!r}"
            )
        return arg

    def _produce_value(self, skip=None) -> None:
        #
        # the same list on every line; loaded once in check_valid()
        #
        self.value = self._values

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
