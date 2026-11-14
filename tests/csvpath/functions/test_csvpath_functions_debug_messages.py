import os
import unittest
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
#
# concat() is evaluated before the condition, so on lines that do not match
# its onmatch qualifier keeps it at its default value
#
CVL = f"""${PATH}[1*][ @c = concat.onmatch("a", "b") #lastname == "Bat" ]"""


def _debug_messages() -> list[str]:
    path = CsvPath()
    path.parse(CVL)
    with unittest.TestCase().assertLogs(path.logger, level="DEBUG") as logs:
        path.collect()
    return [r.getMessage() for r in logs.records]


class TestCsvPathFunctionsDebugMessages(unittest.TestCase):
    def test_default_value_message_is_formatted(self):
        #
        # the message was missing its f prefix, so it logged "{self}"
        # literally
        #
        msgs = [m for m in _debug_messages() if "because !do_onmatch" in m]
        assert len(msgs) == 1
        assert msgs[0].startswith("Concat.concat.onmatch(")
        assert "applying default value, None," in msgs[0]
        assert "{" not in msgs[0]

    def test_do_onmatch_message_still_logged(self):
        msgs = [m for m in _debug_messages() if m.startswith("Qualified.do_onmatch")]
        assert "Qualified.do_onmatch: False for concat" in msgs
        assert "Qualified.do_onmatch: True for concat" in msgs
