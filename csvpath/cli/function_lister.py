import os
import traceback
from csvpath.matching.functions.function_factory import FunctionFactory
from .function_describer import FunctionDescriber
from .selecter import Selecter
from .const import Const


class FunctionLister:
    def __init__(self, cli):
        self._cli = cli

    def list_functions(self) -> None:
        FunctionFactory.load()
        names = list(FunctionFactory.MY_FUNCTIONS.keys())
        names.sort()
        if None in names:
            raise ValueError("None cannot be a key in functions")

        cs = [(n, n) for n in names]

        t = Selecter().ask(title="", values=cs, cancel_value="CANCEL")
        self._cli.clear()
        if t in [Const.CANCEL, Const.CANCEL2]:
            return
        f = FunctionFactory.get_function(
            None, name=t, child=None, find_external_functions=False
        )
        FunctionDescriber.describe(f)
        self._cli._return_to_cont()
