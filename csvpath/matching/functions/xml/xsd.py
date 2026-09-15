import io
import xmlschema
import lxml.etree as etree


from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.productions import Term, Variable
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.args import Args
from csvpath.matching.functions.function_focus import MatchDecider
from csvpath.util.line_spooler import XmlLineSpooler, ListLineSpooler

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos


class Xsd(MatchDecider):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Validates an XML document using an XSD. The project must
                   be configured such that XML docs are acceptable data files.
                   Do this by setting the [inputs] files value to a comma
                   separated string of extensions that includes "xml".

                   If the run is performed by a CsvPaths instance, the XSD
                   parameter must be a file in the named-paths group and just
                   the name of the file, not the full path to the file.

                   If the run is performed programmatically by a CsvPath
                   instance, there is no named-paths group, so the file name
                   parameter must be the full path to the XSD.

                   If validation fails, the errors will be presented as CsvPath
                   Validation Language errors.

                   Validation using an XSD implies an XML document, not
                   line-by-line tabular data. When the validation engine sees
                   the xsd() in your validation, it stops after one data line
                   because the validation of the document is complete.

                   Any of the validation run methods on CsvPaths work with XSD.
                   (e.g. collect_paths). Because there is no enumerated data
                   output from the csvpath statement doing the validation,
                   the run's stop property is set (equivalent to calling the
                   stop() function) after the one line required for validation.
                   That makes fast_forward_paths the most obvious choice for
                   run method.

                   Regardless of run method, multiple XSDs can be applied
                   simply by adding the xsd() function to multiple csvpath
                   statements in the named-paths group.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="XSD file name",
            types=[Term, Variable, Function],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        #
        # set a line spooler that knows XML. there is no chance that
        # we are dealing with anything but XML, unless the user passed in
        # the wrong file or something. if we have a ListLineSpooler or
        # maybe a list, we're fine because we're not writing files.
        #
        if self.matcher.csvpath.lines is not None and not isinstance(
            self.matcher.csvpath.lines, (ListLineSpooler, list)
        ):
            nos = Nos(self.matcher.csvpath.lines.path)
            if nos.exists():
                nos.remove()
            sp = XmlLineSpooler(
                spooler=self.matcher.csvpath.lines,
                source=self.matcher.csvpath.scanner.filename,
            )
            self.matcher.csvpath.lines = sp

    def _produce_value(self, skip=None) -> None:
        xml = self.matcher.csvpath.scanner.filename
        if xml is None:
            raise MatchException("XML document path cannot be None")
        if xml == "":
            raise MatchException("XML document path cannot be the empty string")
        #
        # we have an XSD path and our XML doc, so we have enough to do a validation
        # because we're doing a validation of a non-tabular file we don't continue
        # to more lines.
        #
        self.matcher.csvpath.stop()
        xsd = self._value_one(skip=skip)
        if self.matcher.csvpath.csvpaths is not None:
            npn = self.matcher.csvpath.named_paths_name
            path = self.matcher.csvpath.csvpaths.paths_manager.asset_manager.assets_dir_path(
                npn
            )
            xsd = Nos(path).join(xsd)
        res = self._validate(xsd_path=xsd, xml_path=xml)
        """
        schema = xmlschema.XMLSchema(xsd)
        is_valid = schema.is_valid(xml)
        try:
            schema.validate(xml)
        except xmlschema.XMLSchemaValidationError as e:
            self.value = False
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=f"{e}")
            if self.matcher.csvpath.do_i_raise:
                raise MatchException(f"{e}")
        """
        if isinstance(res, Exception):
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=f"{res}")
            if self.matcher.csvpath.do_i_raise:
                raise MatchException(f"{res}")

        self.value = res is True

    def _validate(self, *, xsd_path: str, xml_path: str) -> bool | Exception:
        xsd = None
        with DataFileReader(xsd_path) as file:
            xsd = file.read()

        xml = None
        with DataFileReader(xml_path) as file:
            xml = file.read()

        xsd_schema = xmlschema.XMLSchema(io.StringIO(xsd))
        xml_root = etree.fromstring(xml.encode())

        # is_valid = xsd_schema.is_valid(xml_root)
        try:
            xsd_schema.validate(xml_root)  # no seek needed — etree Element is reusable
        except xmlschema.XMLSchemaValidationError as e:
            return e
        return True

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.value
