# pylint: disable=C0114
from lxml import etree
from csvpath.matching.util.exceptions import DataException
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class XPath(ValueProducer):
    """returns a substring of a value that is XML using an XPath expression."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
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

    def _produce_value(self, skip=None) -> None:
        xml = self._value_one(skip=skip)
        if xml is None or xml.strip() == "":
            self.value = None
            return
        root = etree.fromstring(xml)
        xpath = self._value_two(skip=skip)
        results = root.xpath(xpath)
        if results and len(results) > 0:
            n = results[0]
            if hasattr(n, "text"):
                n = n.text
            if hasattr(n, "text_content"):
                n = n.text_content()
            else:
                self.value = n

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
