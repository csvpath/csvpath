import os
import io
from contextlib import redirect_stdout
from csvpath.cli.function_describer import FunctionDescriber
from csvpath.matching.functions.function_factory import FunctionFactory


if __name__ == "__main__":

    FunctionFactory.load()
    names = list(FunctionFactory.MY_FUNCTIONS.keys())
    for _ in names:
        f = FunctionFactory.get_function(
            None, name=_, child=None, find_external_functions=False
        )
        ps = io.StringIO()
        with redirect_stdout(ps):
            FunctionDescriber.describe(f, markdown=True)
            docdir = os.path.join(".", "docs", "func_gen")
            if not os.path.exists(docdir):
                os.makedirs(docdir)
            path = os.path.join(docdir, f"{_}.md")
            with open(path, "w") as file:
                file.write(ps.getvalue())
