import unittest
import os
import re
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
        assert (
            problem == f"Jev key in config.ini names env var {name}, which is not set"
        )

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
        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch("csvpath.matching.functions.jev.jev.TypeSafeClient", client),
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
        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch("csvpath.matching.functions.jev.jev.TypeSafeClient", client),
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
        assert (
            f"Jev key in config.ini names env var {name}, which is not set" in messages
        )
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


class _FakeAnswer:
    def __init__(self, **fields) -> None:
        self.__dict__.update(fields)
        self.fields = fields

    def model_dump(self) -> dict:
        return dict(self.fields)


class _FakeResponse:
    def __init__(self, answers: dict) -> None:
        self.model = "jev-fake"
        self.answers = answers


class _FakeClient:
    """stands in for the SDK's TypeSafeClient: answers from the state text
    so that the three live tests' assertions hold, and records the calls"""

    calls = []

    def __init__(self, *, model=None, api_key=None, **kw) -> None:
        self.model = model
        self.api_key = api_key

    def __enter__(self):
        return self

    def __exit__(self, *a) -> None:
        return None

    def system_one(self, *, state, questions):
        _FakeClient.calls.append(
            {"model": self.model, "state": state, "questions": questions}
        )
        text = f"{state}".lower()
        answers = {}
        for k, q in questions.items():
            if q.type == "noul":
                p = 0.9 if re.search(r"\d{2}-\d{4,}", text) else 0.1
                answers[k] = _FakeAnswer(type="noul", noul=p)
            elif q.type == "choice":
                pick = "UK" if "bloody" in text else "US" if "wicked" in text else "AU"
                answers[k] = _FakeAnswer(
                    type="choice",
                    choice=pick,
                    confidence=0.9,
                    probabilities={pick: 0.9},
                )
            else:
                score = {"london": 0.1, "boston": 1.0}.get(text.strip(), 1.9)
                answers[k] = _FakeAnswer(
                    type="score",
                    score=score,
                    confidence=0.9,
                    legend={},
                    probabilities={},
                )
        return _FakeResponse(answers)


class TestCsvPathFunctionsJevFaked(unittest.TestCase):
    """The three live tests' csvpaths, run against a fake client so they run
    without a key and never reach Jev. They test the CVL side: the
    request jev() builds and what it does with the answers."""

    def setUp(self) -> None:
        _FakeClient.calls = []
        self.patches = [
            mock.patch(
                "csvpath.matching.functions.jev.jev.TypeSafeClient", _FakeClient
            ),
            mock.patch.object(Jev, "key_problem", return_value=None),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()

    def test_function_jev_noul_faked(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise ~
            ${PATH}[*][
                @answers = jev(
                    concat(line_values_stack(), ""),
                    noul("This includes a bank account number")
                )
                peek_gt("answers", 0, 0.5) -> @warning = line_number()
            ]"""
        )
        path.fast_forward()
        assert path.variables.get("warning") == 1
        #
        # one request per line, the header included, each with one question
        #
        assert len(_FakeClient.calls) == 4
        assert all(len(c["questions"]) == 1 for c in _FakeClient.calls)
        assert "80-0718281004" in _FakeClient.calls[1]["state"]

    def test_function_jev_choice_faked(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise ~
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
                push("choices", jsonpath(peek("answers", 0), "$.choice"))
            ]"""
        )
        path.fast_forward()
        assert path.variables.get("choices") == ["UK", "US", "AU"]
        q = _FakeClient.calls[0]["questions"]["0"]
        assert q.type == "choice"
        assert sorted(q.criteria) == ["AU", "UK", "US"]

    def test_function_jev_score_faked(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise ~
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
                push("scores", jsonpath(peek("answers", 0), "$.score"))
            ]"""
        )
        path.fast_forward()
        assert path.variables.get("scores") == [0.1, 1.0, 1.9]
        q = _FakeClient.calls[0]["questions"]["0"]
        assert q.type == "score"
