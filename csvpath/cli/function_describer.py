# pylint: disable=C0114
import textwrap
from tabulate import tabulate
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.types.type import Type
from csvpath.matching.functions.function_focus import ValueProducer, MatchDecider
from .const import Const


class FunctionDescriber:
    @classmethod
    def describe(cls, function: Function) -> None:
        if not function.args:
            #
            # today this will most of the time blow up because we're
            # doing a structural validation of a function that is not
            # part of a structure. this should be refactored at some
            # point, but it's not hurting anything.
            #
            try:
                function.check_valid()
            except Exception:
                ...
        if function.description and len(function.description) > 0:
            for i, _ in enumerate(function.description):
                print(_)
                print()
        cls.print_tables(function)

    @classmethod
    def sigs(cls, function):
        sigs = []
        args = function.args
        if not args:
            #
            # this is possibly due to the very small number of unrefactored functions. (3?)
            #
            return sigs
        argsets = args.argsets
        for ai, a in enumerate(argsets):
            pa = ""
            for i, _ in enumerate(a.args):
                t = ""
                if _.name is not None:
                    t += f"{_.name}: "
                for j, act in enumerate(_.actuals):
                    an = cls._actual_name(act)
                    if an == "":
                        an = "''"
                    t += f"{Const.SIDEBAR_COLOR}{Const.ITALIC}{an}{Const.REVERT}"
                    if j < len(_.actuals) - 1:
                        t += "|"
                if _.is_noneable:
                    pa += f"[{t}]"
                else:
                    pa += t
                if i < len(a.args) - 1:
                    pa += ", "
            if a.max_length == -1:
                pa += ", ..."
            pa = pa.strip()
            if pa != "":
                pa = f" {pa} "
            sigs.append(f"{function.name}({pa})")
        return sigs

    @classmethod
    def funcs(cls, function):
        sigs = []
        args = function.args
        argsets = args.argsets
        for ai, a in enumerate(argsets):
            pa = ""
            for i, _ in enumerate(a.args):
                t = ""
                if _.name is not None:
                    t += f"{_.name}: "
                for j, act in enumerate(_.types):
                    an = cls._actual_name(act)
                    if an == "":
                        an = "''"
                    t += f"{Const.SIDEBAR_COLOR}{Const.ITALIC}{an}{Const.REVERT}"
                    if j < len(_.types) - 1:
                        t += "|"
                if _.is_noneable:
                    pa += f"[{t}]"
                else:
                    pa += t
                if i < len(a.args) - 1:
                    pa += ", "
            if a.max_length == -1:
                pa += ", ..."
            pa = pa.strip()
            if pa != "":
                pa = f" {pa} "
            sigs.append(f"{function.name}({pa})")
        return sigs

    @classmethod
    def focus_stmt(cls, function):
        stmts = []
        vp = isinstance(function, ValueProducer)
        md = isinstance(function, MatchDecider)
        if vp and md:
            stmts.append(
                f"{function.name}() produces a calculated value and decides matches"
            )
        elif vp:
            stmts.append(f"{function.name}() produces a calculated value")
        elif md:
            stmts.append(f"{function.name}() determines if lines match")
        else:
            stmts.append(f"{function.name}() is a side-effect")
        return stmts

    @classmethod
    def type_stmt(cls, function):
        stmts = []
        if isinstance(function, Type):
            t = f"{function.name[0].upper()}{function.name[1:]}"
            stmts.append(f"{t} is a line() schema type")
        return stmts

    @classmethod
    def aliases_stmt(cls, function):
        stmts = []
        if len(function.aliases) > 0:
            stmts.append(", ".join(function.aliases))
        return stmts

    @classmethod
    def print_tables(cls, function):
        #
        # data sigs
        #
        headers = ["Data signatures"]
        rows = []
        sigs = cls.sigs(function)
        for v in sigs:
            v = str(v)
            rows.append([v])
        if len(rows) > 0:
            print(tabulate(rows, headers=headers, tablefmt="simple_grid"))
        #
        # call sigs
        #
        headers = ["Call signatures"]
        rows = []
        sigs = cls.funcs(function)
        for v in sigs:
            v = str(v)
            rows.append([v])
        if len(rows) > 0:
            print(tabulate(rows, headers=headers, tablefmt="simple_grid"))
        #
        # type and focus
        #
        rows = []
        headers = []
        stmts = cls.focus_stmt(function)
        for v in stmts:
            v = str(v)
            rows.append(["Focus", v])
        stmts = cls.type_stmt(function)
        for v in stmts:
            v = str(v)
            rows.append(["Type", v])
        stmts = cls.aliases_stmt(function)
        for v in stmts:
            v = str(v)
            rows.append(["Aliases", v])
        if len(rows) > 0:
            print(tabulate(rows, headers=headers, tablefmt="simple_grid"))
        #
        # qualifiers
        #
        rows = []
        headers = []
        stmts = function.match_qualifiers
        stmts = [f"{Const.SIDEBAR_COLOR}{Const.ITALIC}{s}{Const.REVERT}" for s in stmts]
        if len(stmts) > 0:
            rows.append(["Match qualifiers", ", ".join(stmts)])
        stmts = function.value_qualifiers
        stmts = [f"{Const.SIDEBAR_COLOR}{Const.ITALIC}{s}{Const.REVERT}" for s in stmts]
        if len(stmts) > 0:
            rows.append(["Value qualifiers", ", ".join(stmts)])
        if function.name_qualifier:
            rows.append(
                [
                    "Name qualifier",
                    f"{Const.SIDEBAR_COLOR}{Const.ITALIC}optionally expected{Const.REVERT}",
                ]
            )
        if len(rows) > 0:
            print(tabulate(rows, headers=headers, tablefmt="simple_grid"))

    @classmethod
    def _actual_name(cls, a) -> str:
        an = f"{a}"
        if an.rfind("'>") > -1:
            an = an[0 : an.rfind("'>")]
        if an.rfind(".") > -1:
            an = an[an.rfind(".") + 1 :]
        if an.rfind("'") > -1:
            an = an[an.rfind("'") + 1 :]
        return an
