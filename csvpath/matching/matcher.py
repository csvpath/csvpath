from typing import Any, List
from ..util.parser_utility import ParserUtility
from .productions import *
from .functions.function_factory import FunctionFactory
from .functions.function import Function
from .util.expression_encoder import ExpressionEncoder
from .util.exceptions import MatchException
from ..util.exceptions import VariableException
from ..util.exceptions import ConfigurationException
from . import LarkParser, LarkTransformer


class Matcher:
    def __init__(self, *, csvpath=None, data=None, line=None, headers=None):
        if not headers:
            # this could be a dry-run or unit testing
            pass
        if not data:
            raise MatchException(f"need data input: data: {data}")
        self.path = data
        self.csvpath = csvpath
        self._line = line
        self.expressions = []
        self.if_all_match = []
        self.current_expression = None
        self.skip = False
        if data is not None:
            self.parser = LarkParser()
            tree = self.parser.parse(data)
            transformer = LarkTransformer(self)
            es = transformer.transform(tree)
            expressions = []
            for e in es:
                expressions.append([e, None])
            self.expressions = expressions
            self.check_valid()
        if self.csvpath:
            self.csvpath.logger.info("initialized Matcher")

    def __str__(self):
        return f"""
            line: {self.line}
            csvpath: {self.csvpath}
            parser: {self.parser}
        """

    @property
    def line(self) -> List[List[Any]]:
        return self._line

    @line.setter
    def line(self, line: List[List[Any]]) -> None:
        self._line = line

    def to_json(self, e) -> str:
        return ExpressionEncoder().to_json(e)

    def dump_all_expressions_to_json(self) -> str:
        return ExpressionEncoder().valued_list_to_json(self.expressions)

    def reset(self):
        for expression in self.expressions:
            expression[1] = None
            expression[0].reset()
        self.current_expression = None

    def header_index(self, name: str) -> int:
        return self.csvpath.header_index(name)

    def header_name(self, i: int) -> str:
        if not self.csvpath.headers:
            return None
        if i < 0 or i >= len(self.csvpath.headers):
            return None
        return self.csvpath.headers[i]

    def header_value(self, name: str) -> Any:
        n = self.header_index(name)
        ret = None
        if n is None:
            pass
        else:
            ret = self.line[n]
        return ret

    def _do_lasts(self) -> None:
        for i, et in enumerate(self.expressions):
            e = et[0]
            self._find_and_actvate_lasts(e)

    def _find_and_actvate_lasts(self, e) -> None:
        cs = e.children[:]
        while len(cs) > 0:
            c = cs.pop()
            if (
                isinstance(c, Equality)
                and c.op == "->"
                and c.left
                and isinstance(c.left, Function)
                and c.left.name == "last"
            ):
                c.matches(skip=[])
            elif isinstance(c, Function) and c.name == "last":
                c.matches(skip=[])
            else:
                cs += c.children

    def matches(self, *, syntax_only=False) -> bool:
        #
        # is this a blank last line? if so, we just want to activate any/all
        # last() in the csvpath.
        #
        if self.csvpath.line_monitor.is_last_line_and_empty(self.line):
            self._do_lasts()
            return True

        ret = True
        failed = False
        self.current_expression = None
        for i, et in enumerate(self.expressions):
            if self.csvpath and self.csvpath.stopped:
                #
                # stopped is like a system halt. this csvpath is calling it
                # quits on this CSV file. we don't continue to match the row
                # so we may miss out on some side effects. we just return
                # because the function already let the CsvPath know to stop.
                #
                return False
            elif self.skip is True:
                #
                # skip is like the continue statement in a python loop
                # we're not only not matching, we don't want any side effects
                # we might gain from continuing to check for a match;
                # but we also don't want to stop the run or fail validation
                #
                self.skip = False
                return False
            self.current_expression = et[0]
            if et[1] is True:
                ret = True
            elif et[1] is False:
                ret = False
            elif not et[0].matches(skip=[]) and not syntax_only:
                et[1] = False
                ret = False
            else:
                et[1] = True
                ret = True
            if not ret:
                failed = True
            #
            # if we're failed we need to (re)set ret in case this is the final iteration.
            #
            if failed:
                ret = False
        if ret is True:
            self.do_set_if_all_match()
        else:
            pass
        #
        # here we could be set to do an OR, not an AND.
        # we would do that only in the case that the answer was False. if so, we
        # would recheck all self.expressions[.][1] for a True. if at least one
        # were found, we would respond True; else, False.
        #
        return ret

    def check_valid(self) -> None:
        for _ in self.expressions:
            _[0].check_valid()

    def do_set_if_all_match(self) -> None:
        for _ in self.if_all_match:
            name = _[0]
            value = _[1]
            tracking = _[2]
            self.set_variable(name, value=value, tracking=tracking)
        self.if_all_match = []

    def set_if_all_match(self, name: str, value: Any, tracking=None) -> None:
        self.if_all_match.append((name, value, tracking))

    def get_variable(self, name: str, *, tracking=None, set_if_none=None) -> Any:
        if self.csvpath is None:
            return None
        else:
            return self.csvpath.get_variable(
                name, tracking=tracking, set_if_none=set_if_none
            )

    def set_variable(self, name: str, *, value: Any, tracking=None) -> None:
        return self.csvpath.set_variable(name, value=value, tracking=tracking)

    def last_header_index(self) -> int:
        if self.line and len(self.line) > 0:
            return len(self.line) - 1
        return None

    def last_header_name(self) -> str:
        if self.csvpath.headers and len(self.csvpath.headers) > 0:
            return self.csvpath.headers[self.last_header_index()]
        return None
