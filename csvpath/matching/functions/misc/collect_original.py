# pylint: disable=C0114
from csvpath.util.original_file_utility import OriginalFileUtility as orut
from csvpath.util.nos import Nos
from ..function_focus import SideEffect
from ..args import Args


class CollectOriginal(SideEffect):
    """copies the run's registered data file into the result as original.<ext>"""

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                    Copies the registered data file the run started from into the
                    run's results as the well-known file original.<ext>, byte for
                    byte, e.g. original.csv, original.xml, original.json, or
                    original.xlsx. It is the registered file in every source mode:
                    with source-mode: preceding it is still the registered file,
                    not the preceding csvpath's data.csv.

                    data.csv is unchanged: it still holds the matched lines.
                    original.<ext> is fingerprinted in the run's manifest.

                    The copy is made once, the first time collect_original() is
                    evaluated, so it can be conditional, e.g.
                    last() -> collect_original(). It always matches, so rules over
                    a whole XML or JSON document do not need .nocontrib to keep
                    the original with the results.

                    collect_original() needs a CsvPaths run. With a CsvPath alone
                    there is no results directory and it does nothing. Each
                    csvpath in a named-paths group that calls it gets its own
                    copy.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    #
    # the copy is made once per run. not cleared by reset().
    #
    _copied: bool = False

    def _produce_value(self, skip=None) -> None:
        if self._copied:
            return
        self._copied = True
        csvpath = self.matcher.csvpath
        source = csvpath.origin_data_file
        result = getattr(csvpath.lines, "result", None)
        if source is None or result is None:
            csvpath.logger.info(
                "collect_original() has nothing to do: it needs a CsvPaths run with a registered file"
            )
            return
        if not isinstance(source, str):
            csvpath.logger.info(
                "collect_original() expects one registered file, not %s", source
            )
            return
        if not Nos(orut.source_path(source)).exists():
            #
            # e.g. an in-memory source registered in DataFileReader.DATA
            #
            csvpath.logger.info(
                "collect_original() found no file to copy at %s", source
            )
            return
        self.value = orut.copy_original(source=source, instance_dir=result.instance_dir)
        csvpath.logger.info("collect_original() copied %s to %s", source, self.value)

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
