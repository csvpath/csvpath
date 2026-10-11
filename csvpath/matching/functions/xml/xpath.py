# pylint: disable=C0114
import math
from lxml import etree
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class XPath(ValueProducer):
    """returns a substring of a value that is XML using an XPath expression."""

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Finds the value of an XPath expression given a match component containing XML.
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
        self.args.validate(self.siblings())
        super().check_valid()

    #
    # True when the XPath selected something on this line. the match comes
    # from the selection, not the value: an element with no text is still
    # selected.
    #
    _selected: bool = False

    def reset(self) -> None:
        super().reset()
        self._selected = False

    def _produce_value(self, skip=None) -> None:
        self._selected = False
        xml = self._value_one(skip=skip)
        if xml is None or xml.strip() == "":
            self.value = None
            return
        #
        # bytes, because lxml refuses a str that has an encoding declaration
        #
        root = etree.fromstring(xml.encode("utf-8"))
        xpath = self._value_two(skip=skip)
        results = root.xpath(xpath)
        if isinstance(results, list):
            #
            # a node-set. the value is the first node's text.
            #
            self._selected = len(results) > 0
            if self._selected:
                n = results[0]
                if hasattr(n, "tag") and isinstance(n.tag, str):
                    #
                    # an element: all its text, including its children's
                    #
                    self.value = "".join(n.itertext())
                elif hasattr(n, "tag"):
                    #
                    # a comment or processing instruction
                    #
                    self.value = n.text
                else:
                    #
                    # attribute values and text() results are str subclasses
                    #
                    self.value = str(n)
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

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self._selected
