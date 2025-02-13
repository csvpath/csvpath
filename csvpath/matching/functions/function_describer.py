# pylint: disable=C0114
from csvpath.matching.functions.function import Function


class FunctionDescriber:
    def describe(cls, function: Function) -> None:
        args = function.args
        argsets = args.argsets
        for a in argsets:
            pa = ""
            for i, _ in enumerate(a.args):
                if _.is_noneable:
                    pa += "[T]"
                else:
                    pa += "T"
                if i < len(args) - 1:
                    pa += ", "
            print(f"{function.name}({pa})")
