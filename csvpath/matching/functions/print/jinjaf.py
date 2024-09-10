# pylint: disable=C0114
import copy
from typing import Dict, Any, List
from csvpath.matching.productions import Matchable
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.print_parser import PrintParser
from ..function_focus import SideEffect


class Jinjaf(SideEffect):
    """uses Jinja to transform a template using csvpath to get
    values. this is basically a fancy (and slow) form
    of print()."""

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name, child=child)
        self._engine = None

    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        siblings = self.children[0].commas_to_list()

        template_path = siblings[0].to_value(skip=skip)
        if template_path is None or f"{template_path}".strip() == "":
            raise ChildrenException("Jinja function must provide two file paths")
        output_path = siblings[1].to_value(skip=skip)
        if output_path is None or f"{output_path}".strip() == "":
            raise ChildrenException("Jinja function must provide two file paths")

        paths = []
        for i, s in enumerate(siblings):
            if i == 2:
                v = s.to_value(skip=skip)
                paths.append(v)

        page = None
        with open(template_path, "r", encoding="utf-8") as file:
            page = file.read()

        tokens = self._get_tokens(paths)
        page = self._transform(content=page, tokens=tokens)
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(page)

        self.value = self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self._apply_default_match()

    # --------------------

    def _get_tokens(self, paths: List[str]) -> dict:
        tokens = {}
        csvpaths = self.matcher.csvpath.csvpaths
        results_manager = csvpaths.results_manager
        for p in paths:
            results = results_manager.get_named_results(p)
            if len(results) == 0:
                self.matcher.csvpath.logger.warn(
                    "No results for named-results name %s", p
                )
                continue
            r = results[0]
            ts = {}
            tokens[p] = ts
            self._tokens_for_one(ts, r.csvpath)
        ts = {}
        tokens["local"] = ts
        self._tokens_for_one(ts, self.matcher.csvpath)
        return tokens

    def _tokens_for_one(self, tokens: Dict, csvpath) -> None:
        tokens["metadata"] = copy.deepcopy(csvpath.metadata)
        tokens["variables"] = copy.deepcopy(csvpath.variables)
        hs = {}
        for i, h in enumerate(csvpath.headers):
            #
            # the last line could be blank or the wrong number of headers
            # if we can't add a value we'll at least add a blank
            #
            if len(csvpath.matcher.line) > i:
                hs[h] = csvpath.matcher.line[i]
            else:
                hs[h] = ""
        tokens["headers"] = hs
        cs = {}
        printparser = PrintParser(csvpath)
        printparser._get_runtime_data_from_local(csvpath, cs)
        tokens["csvpath"] = cs

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
