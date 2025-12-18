import os
import io
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
    names = list(FunctionFactory.MY_FUNCTIONS.keys())
    for _ in names:
        f = FunctionFactory.get_function(
            None, name=_, child=None, find_external_functions=False
        )
        ps = io.StringIO()
        FunctionDescriber.CONST = MyConst
        with redirect_stdout(ps):
            FunctionDescriber.describe(f, markdown=True)
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
    docdir = os.path.join(".", "docs", "func_gen")
    for _ in names:
        index += f"* [{_}]({docdir}/{_}.md)\n"
    path = os.path.join(docdir, "index.md")
    print(f"path: {path}")
    with open(path, "w") as file:
        file.write(index)
