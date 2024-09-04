# pylint: disable=C0114
from typing import Dict, Any
from .function import Function
from .printf import Print
from ..productions import Matchable
from ..util.exceptions import ChildrenException


class Jinjaf(Function):
    """uses Jinja to transform a template using csvpath to get
    values. this is basically a fancy (and relatively slow) form
    of print()."""

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name, child=child)
        self._engine = None

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        template_path = self.children[0].left.to_value(skip=skip)
        if template_path is None or f"{template_path}".strip() == "":
            raise ChildrenException(
                "Jinja function must have 1 child equality that provides two paths"
            )
        output_path = self.children[0].right.to_value(skip=skip)
        if output_path is None or f"{output_path}".strip() == "":
            raise ChildrenException(
                "Jinja function must have 1 child equality that provides two paths"
            )
        page = None
        with open(template_path, "r", encoding="utf-8") as file:
            page = file.read()
        page = self._transform(content=page, tokens=self._simplify_tokens())
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(page)
        self.value = True

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()

        v = self.to_value(skip=skip)
        return v

    # --------------------

    def _simplify_tokens(self) -> dict:
        ts2 = {}
        ts = Print.tokens(self.matcher)  # pylint: disable=E1101
        # re: E1101: jinja is current broken due to the new print parser, etc.
        # no point fixing this line till the class is rebuilt
        for k, v in ts.items():
            _ = k[2:]
            ts2[_] = v
        return ts2

    def _plural(self, word):
        return self._engine.plural(word)

    def _cap(self, word):
        return word.capitalize()

    def _article(self, word):
        return self._engine.a(word)

    def _transform(self, content: str, tokens: Dict[str, str] = None) -> str:
        from jinja2 import Template, TemplateError  # pylint: disable=C0415
        import inflect  # pylint: disable=C0415
        import traceback  # pylint: disable=C0415

        # re: C0415: leave these imports here. they are super slow.
        # so we don't want the latency in testing or ever unless we're
        # actually rendering a template.

        self._engine = inflect.engine()
        tokens["plural"] = self._plural
        tokens["cap"] = self._cap
        tokens["article"] = self._article
        try:
            template = Template(content)
            content = template.render(tokens)
        except TemplateError:
            print(traceback.format_exc())

        return content
