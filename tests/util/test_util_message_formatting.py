import ast
import os
import re
import unittest
import pytest
from csvpath import CsvPath
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
# deliberate templates, filled in later
#
_TEMPLATE_METHODS = {"replace", "format", "format_map", "substitute"}
_ALLOWED_CALLS = {"cls._load"}
#
# by convention a message is built as msg = "..." and then logged or raised
#
_MESSAGE_NAMES = {"msg", "message"}


def _is_template_call(func: ast.expr) -> bool:
    if ast.unparse(func) in _ALLOWED_CALLS:
        return True
    return isinstance(func, ast.Attribute) and func.attr in _TEMPLATE_METHODS


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
                if isinstance(node, ast.Assign):
                    targets = {t.id for t in node.targets if isinstance(t, ast.Name)}
                    v = node.value
                    if (
                        targets & _MESSAGE_NAMES
                        and isinstance(v, ast.Constant)
                        and isinstance(v.value, str)
                        and _PLACEHOLDER.search(v.value)
                    ):
                        found.append(f"{path}:{v.lineno}: msg = {v.value!r}")
                    continue
                if not isinstance(node, ast.Call) or _is_template_call(node.func):
                    continue
                func = ast.unparse(node.func)
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

    def test_string_length_message_shows_the_lengths(self):
        assert _collected_errors(
            f"$tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv[1][ string(#firstname, 1, 5) ]"
        ) == ["Max length (1) cannot be less than min length (5)"]

    def test_blank_notnone_with_a_header_argument_names_the_header(self):
        #
        # with an argument there is no header position i. a plain f prefix
        # would have raised NameError, because i is only set when there is
        # no argument. the message names the argument's header instead.
        #
        errors = _collected_errors(
            f"$tests{os.sep}csvpath{os.sep}test_resources{os.sep}blank_notnone.csv[1*][ line(string(#a), blank.notnone(#b)) ]"
        )
        assert "Header b cannot be empty because notnone is set" in errors
        assert not any("{" in e for e in errors)

    def test_blank_notnone_without_an_argument_names_the_position(self):
        errors = _collected_errors(
            f"$tests{os.sep}csvpath{os.sep}test_resources{os.sep}blank_notnone.csv[1*][ line(string(#a), blank.notnone()) ]"
        )
        assert "Header 1 cannot be empty because notnone is set" in errors
        assert not any("{" in e for e in errors)


def _collected_errors(cvl: str) -> list[str]:
    path = CsvPath()
    path.parse(f"~ validation-mode: collect, no-raise, no-stop ~ {cvl}")
    path.collect()
    return [e.message for e in path.errors]
