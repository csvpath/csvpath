import traceback
from jsonschema import validate, ValidationError

from csvpath.util.file_readers import DataFileReader
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.productions import Term, Variable
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.args import Args
from csvpath.matching.functions.function_focus import MatchDecider
from csvpath.util.line_spooler import JsonLineSpooler, ListLineSpooler
from csvpath.util.nos import Nos


class JsonSchema(MatchDecider):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Validates an JSON document using an JSONSchema.

                   The project must be configured such that JSON docs are
                   acceptable data files. Do this by setting the
                      [inputs] files
                   value to a comma separated string of extensions that
                   includes "xml".

                   If the run is performed by a CsvPaths instance, the schema
                   parameter must be a file in the named-paths group and just
                   the name of the file, not the full path to the file.

                   If the run is performed programmatically by a CsvPath
                   instance, there is no named-paths group, so the file name
                   parameter must be the full path to the JSONSchema file.

                   If validation fails, the errors will be presented as CsvPath
                   Validation Language errors.

                   Validation using a JSONSchema implies that the data is a
                   JSON document, not a file of line-by-line tabular data.
                   When the validation engine sees the jsonschema() in your
                   validation, it stops after one data line because the
                   validation of the document is complete.

                   Any of the validation run methods on CsvPaths work for
                   JSONSchema. (e.g. collect_paths). Because there is no
                   enumerated data output from the csvpath statement doing the
                   validation, the run's stop property is set (equivalent to
                   calling the stop() function) after the one line required
                   for validation. That makes fast_forward_paths the most
                   obvious choice for run method.

                   Regardless of run method, multiple JSONSchemas can be
                   applied simply by adding the jsonschema() function to
                   multiple csvpath statements in the same named-paths group.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="JSONSchema file name",
            types=[Term, Variable, Function],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        #
        # set a line spooler that knows JSON. there is no chance that
        # we are dealing with anything but JSON, unless the user passed in
        # the wrong file or something. if we have a ListLineSpooler or
        # maybe a list, we're fine because we're not writing files.
        #
        inst = isinstance(self.matcher.csvpath.lines, (ListLineSpooler, list))
        if self.matcher.csvpath.lines is not None and inst is False:
            nos = Nos(self.matcher.csvpath.lines.path)
            if nos.exists():
                nos.remove()
            sp = JsonLineSpooler(self.matcher.csvpath.lines)
            self.matcher.csvpath.lines = sp

    def _produce_value(self, skip=None) -> None:
        file = self.matcher.csvpath.scanner.filename
        if file is None:
            raise MatchException("JSON document path cannot be None")
        if file == "":
            raise MatchException("JSON document path cannot be the empty string")
        #
        # we have a JSONSchema path and our JSON data, so we have enough to do a
        # validation because we're doing a validation of a non-tabular file we
        # stop at the first line scanned.
        #
        self.matcher.csvpath.stop()
        schema = self._value_one(skip=skip)
        if self.matcher.csvpath.csvpaths is not None:
            npn = self.matcher.csvpath.named_paths_name
            path = self.matcher.csvpath.csvpaths.paths_manager.asset_manager.assets_dir_path(
                npn
            )
            schema = Nos(path).join(schema)
        try:
            with DataFileReader(schema) as sr:
                for s in sr.next():
                    schema = s
            with DataFileReader(file) as fr:
                for f in fr.next():
                    file = f
            validate(instance=file, schema=schema)
            self.value = True
        except ValidationError as e:
            self.value = False
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=f"{e}")
            if self.matcher.csvpath.do_i_raise:
                raise MatchException(f"{e}")
        except Exception as e:
            print(traceback.format_exc())
            self.value = False
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=f"{e}")
            if self.matcher.csvpath.do_i_raise:
                raise MatchException(f"{e}")

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.value
