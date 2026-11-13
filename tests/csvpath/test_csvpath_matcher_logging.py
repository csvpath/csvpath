import logging
import os
import unittest
from unittest import mock
from csvpath import CsvPath
from csvpath.matching.productions.expression import Expression

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
CVL = f"""${PATH}[1*][ #lastname == "Bat" ]"""


class TestCsvPathMatcherLogging(unittest.TestCase):
    """Matcher.matches passes each match component to logger.debug as a
    lazy %s argument, so the component's string is only built when debug
    logging is on. Building it eagerly on every line cost 11-20% of a run."""

    def test_components_not_stringified_when_debug_is_off(self):
        path = CsvPath()
        path.parse(CVL)
        path.logger.setLevel(logging.ERROR)
        with mock.patch.object(
            Expression, "__str__", autospec=True, return_value="expr"
        ) as spy:
            lines = path.collect()
        assert len(lines) == 7
        assert spy.call_count == 0

    def test_components_still_logged_when_debug_is_on(self):
        path = CsvPath()
        path.parse(CVL)
        with self.assertLogs(path.logger, level="DEBUG") as logs:
            path.collect()
        msgs = [m for m in logs.output if "ready to adjudicate" in m]
        assert len(msgs) == 8
        assert all("component" in m and "lastname" in m for m in msgs)
