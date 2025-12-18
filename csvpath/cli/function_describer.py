# pylint: disable=C0114
import textwrap
from tabulate import tabulate
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.types.type import Type
from csvpath.matching.functions.function_focus import ValueProducer, MatchDecider
from .const import Const


class FunctionDescriber:

    CONST = Const

    @classmethod
    def const(cls):
        return FunctionDescriber.CONST

    @classmethod
    def describe(
        cls, function: Function, *, markdown=False, const=None, links: dict = None
    ) -> None:
        print("")
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
        if markdown is True:
            print(f"## {function.name}()\n")
        else:
            print(f"{cls.const().BOLD}{function.name}(){cls.const().REVERT}\n")
        if function.description and len(function.description) > 0:
            for i, _ in enumerate(function.description):
                print(_)
                print("")
        cls.print_tables(function, markdown=markdown, links=links)
        print("")
        print(
            "[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]"
        )

    @classmethod
    def sigs(cls, function, *, markdown=False, links: dict = None):
        sigs = []
        args = function.args
        PIPE = " ǁ " if markdown else "|"
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
                    #
                    # add link if exact match and we have links
                    #
                    if markdown and links and an in links:
                        an = f"$${{\\color{{green}}{an}}}$$"

                    if an == "":
                        an = "''"
                    t += f"{cls.const().SIDEBAR_COLOR}{cls.const().ITALIC}{an}{cls.const().REVERT}"
                    if j < len(_.actuals) - 1:
                        t += PIPE
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
    def funcs(cls, function, *, markdown=False, links=None):
        sigs = []
        args = function.args
        PIPE = " ǁ " if markdown else "|"
        if not args or not args.argsets or len(args.argsets) == 0:
            return sigs
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
                    if markdown and links and an in links:
                        an = f"[{an}]({links[an]})"

                    t += f"{cls.const().SIDEBAR_COLOR}{cls.const().ITALIC}{an}{cls.const().REVERT}"
                    if j < len(_.types) - 1:
                        t += PIPE
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
    def focus_stmt(cls, function, *, markdown=False, links=None):
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
    def type_stmt(cls, function, *, markdown=False, links: dict = None):
        stmts = []
        if isinstance(function, Type):
            t = f"{function.name[0].upper()}{function.name[1:]}"
            stmts.append(f"{t} is a line() schema type")
        return stmts

    @classmethod
    def aliases_stmt(cls, function, *, markdown=False, links=None):
        stmts = []
        if len(function.aliases) > 0:
            stmts.append(", ".join(function.aliases))
        return stmts

    @classmethod
    def print_tables(cls, function, *, markdown=False, links: dict = None):
        #
        # data sigs
        #
        headers = ["Data signatures"]
        rows = []
        sigs = cls.sigs(function, markdown=markdown, links=links)
        for v in sigs:
            v = str(v)
            rows.append([v])
        if len(rows) > 0:
            print(
                tabulate(
                    rows,
                    headers=headers,
                    tablefmt="pipe" if markdown else "simple_grid",
                )
            )
            print("")
        #
        # call sigs
        #
        headers = ["Call signatures"]
        rows = []
        sigs = cls.funcs(function, markdown=markdown, links=links)
        for v in sigs:
            v = str(v)
            rows.append([v])
        if len(rows) > 0:
            print(
                tabulate(
                    rows,
                    headers=headers,
                    tablefmt="pipe" if markdown else "simple_grid",
                )
            )
            print("")
        #
        # type and focus
        #
        rows = []
        headers = ["Purpose", "Value"]
        stmts = cls.focus_stmt(function, links=links)
        for v in stmts:
            v = str(v)
            rows.append(["Main focus", v])
        stmts = cls.type_stmt(function, links=links)
        for v in stmts:
            v = str(v)
            rows.append(["Type", v])
        stmts = cls.aliases_stmt(function, links=links)
        for v in stmts:
            v = str(v)
            rows.append(["Aliases", v])
        if len(rows) > 0:
            print(
                tabulate(
                    rows,
                    headers=headers,
                    tablefmt="pipe" if markdown else "simple_grid",
                )
            )
            print("")
        #
        # qualifiers
        #
        rows = []
        headers = ["Context", "Qualifier"]
        stmts = function.match_qualifiers
        stmts = [
            f"{cls.const().SIDEBAR_COLOR}{cls.const().ITALIC}{s}{cls.const().REVERT}"
            for s in stmts
        ]
        if len(stmts) > 0:
            for i, s in enumerate(stmts):
                if markdown and links and s in links:
                    stmts[i] = f"[{s}]({links[s]})"

            rows.append(["Match qualifiers", ", ".join(stmts)])
        stmts = function.value_qualifiers
        stmts = [
            f"{cls.const().SIDEBAR_COLOR}{cls.const().ITALIC}{s}{cls.const().REVERT}"
            for s in stmts
        ]
        if len(stmts) > 0:
            for i, s in enumerate(stmts):
                if markdown and links and s in links:
                    stmts[i] = f"[{s}]({links[s]})"
            rows.append(["Value qualifiers", ", ".join(stmts)])
        if function.name_qualifier:
            rows.append(
                [
                    "Name qualifier",
                    f"{cls.const().SIDEBAR_COLOR}{cls.const().ITALIC}optionally expected{cls.const().REVERT}",
                ]
            )
        if len(rows) > 0:
            print(
                tabulate(
                    rows,
                    headers=headers,
                    tablefmt="pipe" if markdown else "simple_grid",
                )
            )
            print("")

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
