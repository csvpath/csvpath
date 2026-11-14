import ast
import os
import re
import unittest
import pytest
from csvpath.modes.run_mode import RunMode
from csvpath.scanning.scanner2 import Scanner2
from csvpath.scanning.scanner2_transformer import Scanner2Transformer
from csvpath.util.exceptions import InputException
from csvpath.util.json.json_reader_helper import JsonReaderHelper

#
# a plain string holding "{name}" that is passed to a call, e.g. a logger or an
# exception, is almost always a missing f prefix: the reader sees "{name}"
#
_PLACEHOLDER = re.compile(r"\{[A-Za-z_][A-Za-z0-9_\.\[\]\(\)'\"]*\}")
#
# deliberate templates, filled in later by .replace() or .format()
#
_ALLOWED_CALLS = {"f.replace", "cls._load"}


def _unformatted_messages(root: str) -> list[str]:
    found = []
    for dirpath, _, files in os.walk(root):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = ast.unparse(node.func)
                if func in _ALLOWED_CALLS or func.endswith(".format"):
                    continue
                for arg in list(node.args) + [k.value for k in node.keywords]:
                    if (
                        isinstance(arg, ast.Constant)
                        and isinstance(arg.value, str)
                        and _PLACEHOLDER.search(arg.value)
                    ):
                        found.append(f"{path}:{arg.lineno}: {func}({arg.value!r})")
    return found


class _Controller:
    def __init__(self, mode: str):
        self.mode = mode

    def get(self, name: str) -> str:
        return self.mode


class TestUtilMessageFormatting(unittest.TestCase):
    def test_no_unformatted_placeholders_in_messages(self):
        found = _unformatted_messages("csvpath")
        assert found == [], "missing f prefix?\n" + "\n".join(found)

    def test_unknown_run_mode_names_the_mode(self):
        with pytest.raises(InputException, match="Unknown run mode: walk$"):
            RunMode(_Controller("walk")).update()

    def test_scanner_names_the_wrong_type(self):
        with pytest.raises(ValueError, match="not <class 'int'>$"):
            Scanner2().parse(5)

    def test_scanner_transformer_shows_the_value(self):
        with pytest.raises(ValueError, match="not a list: 7$"):
            Scanner2Transformer(Scanner2()).seek(7)

    def test_json_helper_shows_path_and_type(self):
        with pytest.raises(ValueError, match="not a.csv/csv$"):
            JsonReaderHelper._json_type("a.csv", "csv")
