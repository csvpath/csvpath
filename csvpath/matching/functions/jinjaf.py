# pylint: disable=C0114
from typing import Any, Dict
from .function import Function
from .printf import Print
from ..util.exceptions import ChildrenException


class Jinjaf(Function):
    """uses Jinja to transform a template using csvpath to get
    values. this is basically a fancy (and relatively slow) form
    of print()."""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
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
        return True

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()

        v = self.to_value(skip=skip)
        return v

    # --------------------

    def _simplify_tokens(self) -> dict:
        ts2 = {}
        ts = Print.tokens(self.matcher)
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
        #
        # leave these imports here so we don't add latency
        # unless we're actually rendering a template.
        #
        from jinja2 import Template
        import inflect
        import traceback

        self._engine = inflect.engine()

        tokens["plural"] = self._plural
        tokens["cap"] = self._cap
        tokens["article"] = self._article
        try:
            template = Template(content)
            content = template.render(tokens)
        except Exception:
            print(traceback.format_exc())

        return content
