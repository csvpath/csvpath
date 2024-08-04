from typing import Any, Dict
from .function import Function, ChildrenException
from ..productions.equality import Equality
from .printf import Print


class Jinjaf(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) != 1:
            raise ChildrenException("Jinja function must have 1 child")
        if not isinstance(self.children[0], Equality):
            raise ChildrenException(
                "Jinja function must have 1 child equality that provides two paths"
            )
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
        with open(template_path, "r") as file:
            page = file.read()

        page = self._transform(content=page, tokens=self._simplify_tokens())
        with open(output_path, "w") as file:
            file.write(page)
        return True

    def matches(self, *, skip=[]) -> bool:
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

        tokens["plural"] = self._plural
        tokens["cap"] = self._cap
        tokens["article"] = self._article
        try:
            template = Template(content)
            content = template.render(tokens)
        except Exception:
            print(traceback.format_exc())

        return content
