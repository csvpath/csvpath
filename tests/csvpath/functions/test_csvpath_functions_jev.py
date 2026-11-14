import unittest
import os
from unittest import mock
from csvpath import CsvPath
from csvpath.matching.functions.jev.jev import Jev

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}jev.csv"

#
#          ,
#               choice(#word, "a UK phrase", "a US phrase", "an AU phrase"),
#               score(#location, "Mostly warm weather", "Mostly cold weather", "Seasonal weather")
#


def jev_key_available() -> bool:
    """True only when config.ini's [jev] key resolves to a usable key.

    These tests call the live Jev service, so they run only when a key is
    really there. Jev.check_valid() uses the same rule, Jev.key_problem().
    """
    return Jev.key_problem(config=CsvPath().config) is None


class TestJevKeyGate(unittest.TestCase):
    """The gate itself. Never calls Jev: it only checks what the gate returns."""

    def _env_reference(self) -> str:
        config = CsvPath().config
        raw = config.get(section="jev", name="key", swaps=False, string_parse=False)
        if not isinstance(raw, str) or not raw.strip().isupper():
            self.skipTest("[jev] key is not an env var reference in this config")
        return raw.strip()

    def test_gate_closed_when_env_var_unset(self):
        name = self._env_reference()
        env = {k: v for k, v in os.environ.items() if k != name}
        with mock.patch.dict(os.environ, env, clear=True):
            assert jev_key_available() is False

    def test_gate_closed_when_env_var_blank(self):
        name = self._env_reference()
        with mock.patch.dict(os.environ, {name: "   "}):
            assert jev_key_available() is False

    def test_gate_open_when_env_var_set(self):
        name = self._env_reference()
        with mock.patch.dict(os.environ, {name: "not-a-real-key"}):
            assert jev_key_available() is True


class TestJevKeyCheck(unittest.TestCase):
    """Jev.check_valid() fails fast on an unusable key. Never calls Jev: the
    client is patched to fail the test if anything builds it."""

    def _env_reference(self) -> str:
        config = CsvPath().config
        raw = config.get(section="jev", name="key", swaps=False, string_parse=False)
        if not isinstance(raw, str) or not raw.strip().isupper():
            self.skipTest("[jev] key is not an env var reference in this config")
        return raw.strip()

    def test_key_problem_names_the_unset_env_var(self):
        name = self._env_reference()
        env = {k: v for k, v in os.environ.items() if k != name}
        with mock.patch.dict(os.environ, env, clear=True):
            problem = Jev.key_problem(config=CsvPath().config)
        assert problem == f"Jev key in config.ini names env var {name}, which is not set"

    def test_key_problem_none_when_env_var_set(self):
        name = self._env_reference()
        with mock.patch.dict(os.environ, {name: "not-a-real-key"}):
            assert Jev.key_problem(config=CsvPath().config) is None

    def test_key_problem_requires_config(self):
        with self.assertRaises(ValueError):
            Jev.key_problem(config=None)

    def test_jev_with_unset_key_stops_before_calling_jev(self):
        #
        # before, check_valid() only checked for None, so the env var's
        # name was sent to Jev as the key
        #
        name = self._env_reference()
        env = {k: v for k, v in os.environ.items() if k != name}
        client = mock.MagicMock(side_effect=AssertionError("Jev must not be called"))
        with mock.patch.dict(os.environ, env, clear=True), mock.patch(
            "csvpath.matching.functions.jev.jev.TypeSafeClient", client
        ):
            path = CsvPath()
            path.parse(
                f"""
                ~ validation-mode:raise ~
                ${PATH}[*][
                    @answers = jev(
                        concat(line_values_stack(), ""),
                        noul("This includes a bank account number")
                    )
                ]"""
            )
            with self.assertRaises(Exception) as ctx:
                path.fast_forward()
        assert f"names env var {name}, which is not set" in str(ctx.exception)
        assert client.call_count == 0

    def test_jev_with_unset_key_reports_the_problem_without_raise(self):
        #
        # under no-raise the run stops at validation. the error must be
        # collected, or the run looks valid and empty with no reason given.
        #
        name = self._env_reference()
        env = {k: v for k, v in os.environ.items() if k != name}
        client = mock.MagicMock(side_effect=AssertionError("Jev must not be called"))
        with mock.patch.dict(os.environ, env, clear=True), mock.patch(
            "csvpath.matching.functions.jev.jev.TypeSafeClient", client
        ):
            path = CsvPath()
            path.parse(
                f"""
                ~ validation-mode:collect, no-raise, no-stop ~
                ${PATH}[*][
                    @answers = jev(
                        concat(line_values_stack(), ""),
                        noul("This includes a bank account number")
                    )
                ]"""
            )
            path.fast_forward()
        messages = [e.message for e in path.errors]
        assert f"Jev key in config.ini names env var {name}, which is not set" in messages
        assert client.call_count == 0


@unittest.skipUnless(
    jev_key_available(), "no [jev] key in config.ini, or its env var is not set"
)
class TestCsvPathFunctionsJev(unittest.TestCase):
    def test_function_jev_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print~
            ${PATH}[*][
                @answers = jev(
                    concat(line_values_stack(), ""),
                    noul("This includes a bank account number")
                )
                print("answers: $.variables.answers")
                peek_gt("answers", 0, 0.5) -> print("warning $.headers.cargo may have an account number")
                peek_gt("answers", 0, 0.5) -> @warning = line_number()
                peek_lt("answers", 0, 0.5) -> print("false alarm. cargo seems Ok")
                peek_eq("answers", 0, 0.5) -> print("unable to determine if cargo is Ok")
            ]"""
        )
        path.fast_forward()
        assert path.variables.get("warning") == 1

    def test_function_jev_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print~
            ${PATH}[1*][
                @answers = jev(
                    #phrase,
                    choice(
                        "Where is this phrase from?",
                        criteria(
                            "UK", "From England",
                            "US", "From America",
                            "AU", "From Down Under"
                        )
                    )
                )
                push(
                    "choices",
                    jsonpath(peek("answers", 0), "$.choice")
                )

            ]"""
        )
        path.fast_forward()
        assert path.variables.get("choices") == ["UK", "US", "AU"]

    def test_function_jev_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print~
            ${PATH}[1*][
                @answers = jev(
                    #location,
                    score(
                        "Where is this phrase from?",
                            "Mostly cool weather",
                            "Seasonal weather",
                            "Mostly warm weather"
                    )
                )
                @score = jsonpath(peek("answers", 0), "$.score")
                push("scores", @score)
                print("$.headers.location: $.variables.score")
            ]"""
        )
        path.fast_forward()
        scores = path.variables.get("scores")
        assert len(scores) == 3
        orig = scores[:]
        scores.sort()
        assert orig == scores
