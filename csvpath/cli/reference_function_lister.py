from csvpath.references.function_describer_3 import Function3Describer
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from .selecter import Selecter
from .const import Const


class ReferenceFunctionLister:
    """lists every registered references-v3 function and, on selection,
    prints its documentation -- the references-v3 analog of
    FunctionLister/FunctionDescriber, same Selecter-based radio-list
    idiom. Function3Describer already did the hard part (compendium
    5.4's own markdown renderer, wiring it into a CLI explicitly left
    as "a separate integration question" by its own docstring) -- this
    is that integration, David's own CLI request, 2026-10-22. Nested
    under ReferenceRunner's menu rather than a new top-level Cli entry,
    David's choice, since it's thematically the same "working with
    reference-v3" area as "rerun recent"/"new expression"."""

    def __init__(self, cli):
        self._cli = cli

    def list_functions(self) -> None:
        names = sorted(ReferenceFunctionFactory.registered_names())
        cs = [(n, n) for n in names]
        t = Selecter().ask(title="", values=cs, cancel_value=Const.CANCEL)
        self._cli.clear()
        if t in (Const.CANCEL, Const.CANCEL2):
            return
        function_cls = ReferenceFunctionFactory.get_registered_class(t)
        doc = Function3Describer.describe(function_cls, name=t, markdown=False)
        print(doc)
        self._cli._return_to_cont()
