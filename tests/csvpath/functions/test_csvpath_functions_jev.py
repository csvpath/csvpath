import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}jev.csv"

#
#          ,
#               choice(#word, "a UK phrase", "a US phrase", "an AU phrase"),
#               score(#location, "Mostly warm weather", "Mostly cold weather", "Seasonal weather")
#


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
