from csvpath.matching.productions.equality import Equality
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.function import Function

"""
from csvpath.matching.expression_encoder import ExpressionEncoder
from csvpath.matching.expression_utility import ExpressionUtility
"""


class ExpressionMath:
    """this code works up to a point. there are limitations in
    the number of operations and there is no precedence or
    grouping. you can enable math with the CsvPath.do_math()
    toggle but unless you know it will solve a specific problem
    you shouldn't. the grammar needs to be reworked to make
    arithmetic possible without functions, but it isn't a
    priority."""

    def is_terminal(self, o):
        return (
            isinstance(o, Variable)
            or isinstance(o, Term)
            or isinstance(o, Header)
            or isinstance(o, Function)
        )

    def do_math(self, expression):
        for i, _ in enumerate(expression.children):
            self.drop_down_pull_up(expression, i, _)

    def math(self, op, left, right):
        if left is None or right is None:
            raise Exception(
                f"ExpresionMath.math: operands cannot be None: {left}, {right}"
            )
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            return left / right
        else:
            raise Exception(f"op cannot be {op}")

    #
    # why is this not combining the last two terms?
    #
    def combine_terms(self, parent, i, child):
        if isinstance(child, Equality) and child.op in ["-", "+", "*", "/"]:
            lv = child.left.to_value()
            if child.right is not None:
                rv = child.right.to_value()
                term = Term(parent.matcher)
                term.value = self.math(child.op, lv, rv)
                parent.children[i] = term
                term.parent = parent
                return term, i
            else:
                print("not combining terms")
                return child, i
        else:
            print("not an equality with math")
            return child, i

    def push_down_right_terminal(self, parent, i, child):
        eq = isinstance(parent, Equality)
        op = parent.op in ["-", "+", "*", "/"] if eq else None
        """
        print(f"@ push_down_right_terminal: child {ExpressionUtility._dotted('', child)}")
        json2 = ExpressionEncoder().simple_list_to_json([child])
        print(f"@ push_down_right_terminal: child: {json2}")
        """
        if eq and op:
            second = self.is_terminal(child)
            if second:
                third = isinstance(child.parent, Equality) and isinstance(
                    child.parent.left, Equality
                )
                if third:
                    # move child down to left
                    term = Term(child.matcher)
                    try:
                        term.value = self.math(
                            parent.op, child.value, child.parent.left.right.value
                        )
                        child.parent.left.right = term
                        term.parent = child.parent.left
                        # remove child from it's original place now that term includes its value
                        child.parent.right = None
                        replace_me = child.parent.parent.index_of_child(child.parent)
                        child.parent.parent.children[replace_me] = child.parent.left
                    except Exception as ex:
                        print(f"problems? or maybe just mathed out. ex: {ex}")

    def drop_down_pull_up(self, parent, i, child):
        # work right to left
        cs = child.children[:]
        cs.reverse()
        for j, _ in enumerate(cs):
            self.drop_down_pull_up(child, j, _)

        # if we're a terminal within an equality with math and another terminal
        # we want to reduce ourselves before anything else. to do that we need to
        # shortcut to the parent equality
        choose = isinstance(parent, Equality) and parent.op in ["-", "+", "*", "/"]
        if choose and child.parent.both_terminal():
            try:
                x = child.parent.parent.children.index(parent)
                child, i = self.combine_terms(parent.parent, x, parent)
            except Exception:
                print("no such child anymore. presumably mathed out")
                pass
        else:
            # this method won't combine terms in this equality, but we might
            # do a pull-up-push-down below. do we need to make this call?
            child, i = self.combine_terms(parent, i, child)

        self.push_down_right_terminal(parent, i, child)
