import os
import io
from datetime import datetime
from contextlib import redirect_stdout
from csvpath.cli.function_describer import FunctionDescriber
from csvpath.matching.functions.function_factory import FunctionFactory


class MyConst:
    ITALIC = ""
    SIDEBAR_COLOR = ""
    REVERT = ""


if __name__ == "__main__":

    FunctionFactory.load()
    #
    # make pages
    #

    links = {
        "Term": "https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term",
        "Variable": "https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable",
        "Reference": "https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference",
        "Header": "https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header",
        "Function": "https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function",
        "asbool": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#asbool",
        "decrease": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#decrease",
        "distinct": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#distinct",
        "increase": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#increase",
        "latch": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#latch",
        "nocontrib": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#nocontrib",
        "notnone": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#notnone",
        "once": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#once",
        "onchange": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onchange",
        "onmatch": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch",
        "renew": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew",
        "strict": "https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#strict",
        "str": "",
        "int": "",
        "float": "",
        "date": "",
        "datetime": "",
        "None": "",
        "''": "",
        "bool": "",
        "Any": "",
    }

    names = list(FunctionFactory.MY_FUNCTIONS.keys())
    names.sort()
    for _ in names:
        f = FunctionFactory.get_function(
            None, name=_, child=None, find_external_functions=False
        )
        ps = io.StringIO()
        FunctionDescriber.CONST = MyConst
        with redirect_stdout(ps):
            FunctionDescriber.describe(f, markdown=True, links=links)
            docdir = os.path.join(".", "docs", "func_gen")
            if not os.path.exists(docdir):
                os.makedirs(docdir)
            path = os.path.join(docdir, f"{_}.md")
            with open(path, "w") as file:
                file.write(ps.getvalue())
    #
    # make index page
    #
    index = "# Functions Index\n"
    index = f"{index}These function docs are generated from the function code. They are also available in the CsvPath Framework [CLI](https://www.csvpath.org) and [FlightPath Data](https://www.flightpathdata.com).\n"
    index = f"{index}\n\n[[Back to overview](https://github.com/csvpath/csvpath/blob/main/docs/functions.md)]\n\n"
    docdir = os.path.join(".", "docs", "func_gen")
    for _ in names:
        index += f"* [{_}](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/{_}.md)\n"
    index += f"\n\nGenerated on: {datetime.now()}\n"
    path = os.path.join(docdir, "index.md")
    print(f"path: {path}")
    with open(path, "w") as file:
        file.write(index)
