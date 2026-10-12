# pylint: disable=C0114
import math
from lxml import etree
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.document_utility import DocumentUtility as dout
from csvpath.util.line_spooler import CsvLineSpooler, XmlLineSpooler
from csvpath.util.nos import Nos
from ..function import Function
from ..args import Args


class XPath(ValueProducer):
    """returns a substring of a value that is XML using an XPath expression."""

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Finds the value of an XPath expression given a match component containing XML.
                   A path that selects one node gives that node's value, several
                   nodes give a list of their values, and no nodes give an empty
                   list, as with jsonpath(). XPath functions like count(),
                   boolean(), and string() give their result.
                """
            ),
            self.wrap(
                """\
                   With only an XPath, xpath() evaluates the whole data file as one
                   XML document, for rules-based validation of XML files. Each
                   xpath() evaluates the document on one line only: scan [*] and
                   make stop() the last match component, or scan [0] if the file
                   does not start with a blank line. Use .nocontrib on rules like
                   xpath.nocontrib("/orders/order[not(sku)]") -> print("...", fail())
                   so that a conforming document still matches. The run's data is
                   a copy of the document.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="from this XML",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="select this XPath",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a = self.args.argset(1)
        a.arg(
            name="select this XPath in the whole document",
            types=[Term, Variable, Function, Reference],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        if self._is_document_form():
            self._use_document_spooler()

    #
    # True when the XPath selected something on this line. the match comes
    # from the selection, not the value: an element with no text is still
    # selected.
    #
    _selected: bool = False
    #
    # the whole-document form: the parsed document and the line it was
    # evaluated on. not cleared by reset(); they last for the run.
    #
    _document = None
    _document_line: int | None = None

    def reset(self) -> None:
        super().reset()
        self._selected = False

    def _is_document_form(self) -> bool:
        return len(self.siblings()) == 1

    def _use_document_spooler(self) -> None:
        #
        # the run's data is a copy of the XML document, as with xsd(). only
        # swap a CsvLineSpooler: a list needs nothing, and another xpath()
        # in the same csvpath may already have swapped it.
        #
        lines = self.matcher.csvpath.lines
        if isinstance(lines, CsvLineSpooler):
            nos = Nos(lines.path)
            if nos.exists():
                nos.remove()
            self.matcher.csvpath.lines = XmlLineSpooler(
                spooler=lines, source=self.matcher.csvpath.scanner.filename
            )

    def _document_root(self):
        self._document_line = dout.assert_one_line(
            function=self, first_line=self._document_line
        )
        if self._document is None:
            text = dout.read_document(function=self)
            #
            # bytes, because lxml refuses a str that has an encoding declaration
            #
            self._document = etree.fromstring(text.encode("utf-8"))
        return self._document

    def _produce_value(self, skip=None) -> None:
        self._selected = False
        if self._is_document_form():
            root = self._document_root()
            xpath = self._value_one(skip=skip)
        else:
            xml = self._value_one(skip=skip)
            if xml is None or xml.strip() == "":
                self.value = None
                return
            #
            # bytes, because lxml refuses a str that has an encoding declaration
            #
            root = etree.fromstring(xml.encode("utf-8"))
            xpath = self._value_two(skip=skip)
        self._set_from_results(root.xpath(xpath))

    def _set_from_results(self, results) -> None:
        if isinstance(results, list):
            #
            # a node-set. as with jsonpath(): one node gives its value,
            # several give a list of values in document order, none gives [].
            #
            self._selected = len(results) > 0
            values = [self._node_value(n) for n in results]
            self.value = values[0] if len(values) == 1 else values
        elif isinstance(results, bool):
            self.value = results
            self._selected = results
        elif isinstance(results, float):
            self.value = results
            self._selected = not math.isnan(results)
        else:
            #
            # string() and other string results. lxml gives a str subclass
            #
            self.value = str(results)
            self._selected = self.value != ""

    def _node_value(self, n):
        if hasattr(n, "tag") and isinstance(n.tag, str):
            #
            # an element: all its text, including its children's
            #
            v = "".join(n.itertext())
        elif hasattr(n, "tag"):
            #
            # a comment or processing instruction
            #
            v = n.text
        else:
            #
            # attribute values and text() results are str subclasses
            #
            v = str(n)
        #
        # strip, as to_value() strips a single string value
        #
        return v.strip() if isinstance(v, str) else v

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self._selected
