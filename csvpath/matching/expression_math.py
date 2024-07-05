from csvpath.matching.productions.equality import Equality
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.function import Function

class ExpressionMath:

    def __init__(self, matcher):
        self._matcher = matcher

    def is_terminal(self, o):
        return isinstance( o, Variable) or isinstance( o, Term) or isinstance( o, Header) or isinstance( o, Function)

    def do_math(self, expression):
        for i, _ in enumerate(expression.children):
            self.pull_up(expression, i, _)

    def try_2_terms(self, parent, i, child):
        if self.is_terminal(child.left) and self.is_terminal(child.right):
            term = Term(self._matcher)
            term.value = self.math( child.op, child.left.to_value(), child.right.to_value())
            parent.children[i] = term

    def try_mathy_left_term_right(self, parent, i, child):
        if isinstance(child.left, Equality) and self.is_terminal(child.right):
            # value of  -> child.left.left.value
            v = child.right.to_value()
            child.left.right.to_value()
            child.left.right.value = self.math(child.op, child.left.right.value, v)
            # parent[i] = child.right
            parent.children[i] = child.left
            child.left.parent = parent
            # child.right.parent = parent

    def pull_up(self, parent, i, child):
        if isinstance( child, Equality ) and child.op in ['-','+','*','/']:
            self.try_2_terms(parent, i, child)
            self.try_mathy_left_term_right(parent, i, child)
        else:
            for j, desc in enumerate(child.children):
                self.pull_up(child, j, desc)

    def math(self, op, left, right ):
        if op == '+':
            return left+right
        elif op == '-':
            return left-right
        elif op == '*':
            return left*right
        else:
            return left/right
