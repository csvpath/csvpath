import unittest
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.expression_utility import ExpressionUtility

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"
NUMBERS = "tests/test_resources/numbers.csv"


class TestFunctions(unittest.TestCase):

    # ============= count ================

    def test_function_factory(self):
        count = FunctionFactory.get_function(None, name="count", child=None)
        assert count

    def test_function_count_empty(self):
        f = FunctionFactory.get_function(None, name="count", child=None)
        assert f.to_value() == 0  # no matcher or csvpath == -1 + eager match 1

    def test_function_count_equality(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][count(#lastname=="Bat")==7]')
        lines = path.collect()
        print(f"test_function_count_equality: lines: {lines}")
        assert len(lines) == 1
        assert lines[0][0] == "Frog"

    def test_function_header_in(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][in(#firstname,"Bug|Bird|Ants")]')
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 3

    def test_function_qualifier(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            @t.onmatch=count.firstname_match(#firstname=="Ants")
                            #firstname=="Ants"
                        ]
                   """
        )
        lines = path.collect()
        print(f"test_function_qualifier: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_qualifier: line: {line}")
        print(f"test_function_qualifier: path vars: {path.variables}")
        assert len(lines) == 1
        assert "firstname_match" in path.variables
        assert path.variables["firstname_match"][True] == 1

    def test_function_every_qualifier1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            @t.onmatch=count()
                            every.fish(#lastname=="Bat", 2)
                            #lastname=="Bat"
                        ]
                   """
        )
        #
        # we capture 1 #lastname!="Bat" because there are 2 such lines
        # and we capture 3 #lastname=="Bat" because there are 7 such lines
        #
        lines = path.collect()
        print(f"test_function_every_qualifier: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_every_qualifier: line: {line}")
        print(f"test_function_every_qualifier: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["t"] == 3
        assert "fish" in path.variables
        assert path.variables["fish"][True] == 4

    def test_function_every_qualifier2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            @t.onmatch=count()
                            every.who(#lastname, 2)
                        ]
                   """
        )
        #
        # we capture 3 #lastnames because there are 3 total in 9
        # and we match on 3 #lastnames because there are 7 "Bat"
        #
        lines = path.collect()
        print(f"test_function_every_qualifier: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_every_qualifier: line: {line}")
        print(f"test_function_every_qualifier: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["t"] == 3
        assert "who" in path.variables
        assert path.variables["who"][True] == 3

    def test_function_count_header_in_2(self):
        path = CsvPath()
        path.parse(
            f"""
                        ${PATH}
                        [*]
                        [count.firstname_is_one(in(#firstname,"Bug|Bird|Ants"))==2]
                   """
        )
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 1
        assert "firstname_is_one" in path.variables
        assert path.variables["firstname_is_one"][True] == 3

    def test_function_count_header_in_ever(self):
        path = CsvPath()
        path.parse(
            f"""
                ${PATH}
                [*]
                [
                    @x.onmatch = count()
                    in(#firstname,"Bug|Bird|Ants")
                ]
                   """
        )
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "x" in path.variables
        assert path.variables["x"] == 3
        assert len(lines) == 3

    def test_function_percent(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][@p = percent("match") #lastname=="Bat"]')
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 7
        assert path.variables["p"] == 0.75

    def test_function_below_percent(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][@p = percent("match")  below(@p,.35) #lastname=="Bat"]')
        lines = path.collect()
        print(f"test_function_below_percent: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_below_percent: line: {line}")
        print(f"test_function_below_percent: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["p"] == 0.375

    def test_function_tally1(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][tally(#lastname) no()] ")
        path.collect()
        print(f"test_function_tally: path vars: {path.variables}")
        assert path.variables["lastname"]["Bat"] == 7

    def test_function_tally2(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][tally(#firstname, #lastname)] ")
        path.collect()
        print(f"test_function_tally: path vars: {path.variables}")
        assert path.variables["tally"]["Frog|Bat"] == 2

    def test_function_first1(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][first.surnames(#lastname)]")
        lines = path.collect()
        print(f"test_function_first: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_first: line: {line}")
        print(f"test_function_first: path vars: {path.variables}")
        for _ in path.variables:
            print(f"  ..._:{_}")
            for k, v in enumerate(path.variables[_].items()):
                print(f"     ... {k} = {v}")
        assert len(lines) == 3
        assert "surnames" in path.variables
        assert path.variables["surnames"]["Bat"] == 2

    def test_function_first2(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][first.folks(#firstname)]")
        lines = path.collect()
        print(f"test_function_first: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_first: line: {line}")
        print(f"test_function_first: path vars: {path.variables}")
        assert len(lines) == 8
        assert "folks" in path.variables
        assert path.variables["folks"]["Frog"] == 3

    def test_function_first3(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][first.dude(#firstname, #lastname)]")
        lines = path.collect()
        print(f"test_function_first: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_first: line: {line}")
        print(f"test_function_first: path vars: {path.variables}")
        assert len(lines) == 8
        assert "dude" in path.variables
        assert path.variables["dude"]["FrogBat"] == 3

    def test_function_above_percent(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][@p=percent("line")  above(@p, .35) #lastname=="Bat"]')
        lines = path.collect()
        print(f"test_function_above_percent: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_above_percent: line: {line}")
        print(f"test_function_above_percent: path vars: {path.variables}")
        assert len(lines) == 6
        assert path.variables["p"] == 1

    def test_function_upper_and_lower(self):
        path = CsvPath()
        path.parse(
            f"${PATH}[*][ @upper = upper(#firstname) @lower = lower(#firstname) ]"
        )
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "upper" in path.variables
        assert "lower" in path.variables
        assert path.variables["lower"] == "frog"
        assert path.variables["upper"] == "FROG"

    def test_function_count_lines(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][ #firstname=="David" @david.onmatch=count_lines() ]')
        lines = path.collect()
        assert len(lines) == 1
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["david"] == 1

    def test_function_count_scans(self):
        path = CsvPath()
        path.parse(
            f'${PATH}[*][ #firstname=="Frog" @frogs_seen=count() @scanned_for_frogs=count_scans()  ]'
        )
        lines = path.collect()
        assert len(lines) == 2
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["frogs_seen"] == 2
        assert path.variables["scanned_for_frogs"] == 9

    """
    TODO: need a way to only count complete path matches
    """

    def test_function_the_first_two_lines(self):
        path = CsvPath()
        # this returns the first two lines because first collects
        # the first instance of every value matched, so 0 and 1 for False and True
        path.parse(f"${PATH}[*][ first(count()==1)]")
        lines = path.collect()
        print(f"test_function_first_two_lines: path vars: {path.variables}")
        assert len(lines) == 2

    def test_function_the_first_line(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                count.firstname(#firstname=="Frog")==1
                @say.onmatch=#say
                @line.onmatch=count_lines()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: lines: {lines}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["say"] == "ribbit..."
        assert path.variables["line"] == 3

    def test_function_any_match(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                or(#firstname=="Fish", #lastname=="Kermit", #say=="oozeeee...")
                @say.onmatch=#say
                @line.onmatch=count_lines()

            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: lines: {lines}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["say"] == "oozeeee..."
        assert path.variables["line"] == 7

    def test_function_length(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = length("this") ]"""
        )
        lines = path.collect()
        print(f"test_function_length: lines: {lines}")
        print(f"test_function_length: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 4

    def test_function_add1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( 4, length("this")) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 8

    def test_function_add2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_add3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_add4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5, 5 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 15

    def test_function_subtract(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == -3

    def test_function_subtract2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_subtract3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this"), add( 2, 3) ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 0

    def test_function_multiply(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-5]
            [ @l = multiply( count(#lastname), 100 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 4
        assert path.variables["l"] == 400

    def test_function_multiply2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = multiply( count(), 100 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 200

    def test_function_multiply3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2+3]
            [ @l = multiply( count(), add(50,50,50,50) ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 400

    def test_function_multiply4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2+3]
            [ @l = multiply( count(), add(50,50,50), 50 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 15000

    def test_function_divide(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2]
            [ @l = divide( 100, 10 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_divide2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, count() ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 50

    def test_function_divide3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, count(), add(2,3) ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 10

    def test_function_divide4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, 0 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 2
        import math

        assert math.isnan(path.variables["l"])

    def test_function_count_any_match(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @interesting.onmatch = count()
                or(#firstname=="Fish", #lastname=="Kermit", #say=="oozeeee...")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["interesting"] == 3
        assert len(lines) == 3

    def test_function_nocount(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][ @imcounting = count() no()]
            """
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "imcounting" not in path.variables
        assert len(lines) == 0

    def test_function_allcount(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][ @imcounting = count() yes()]
            """
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "imcounting" in path.variables
        assert path.variables["imcounting"] == 9
        assert len(lines) == 9

    def test_function_linecount(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][ @imcounting = count_lines() no()]
            """
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "imcounting" in path.variables
        # lines are zero-based, unlike match counts
        assert path.variables["imcounting"] == 8
        assert len(lines) == 0

        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][ @imcounting.onmatch = count_lines() no()]
            """
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "imcounting" not in path.variables
        # lines are zero-based, unlike match counts
        # assert path.variables["imcounting"] == 0
        assert len(lines) == 0

    def test_function_every1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                every(#lastname=="Bat", 3 )
            ]"""
        )
        lines = path.collect()
        print(f"test_function_every: path vars: {path.variables}")
        print(f"lines: {lines}")
        assert len(lines) == 2

    def test_function_yes(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                yes()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_every: path vars: {path.variables}")
        print(f"lines: {lines}")
        assert len(lines) == 9

    def test_function_end(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @end = end()
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["end"] == "growl"
        assert len(lines) == 0

    def test_function_max(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_max = max(#firstname)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["the_max"] == "Slug"
        assert len(lines) == 0

        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_max = max(#0)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["the_max"] == "firstname"
        assert len(lines) == 0

    def test_function_min(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_min = min(#firstname)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["the_min"] == "Ants"
        assert len(lines) == 0

        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_min = min(#firstname, "scan")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["the_min"] == "Bird"
        assert len(lines) == 0

        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_min = min(#firstname, "match")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_min: path vars: {path.variables}")
        assert path.variables["the_min"] is None
        assert len(lines) == 0

    def test_function_average(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_average = average(count(), "match")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_count_in: path vars: {path.variables}")
        assert path.variables["the_average"] is None
        assert len(lines) == 0

        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_average = average(count(#lastname), "scan")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["the_average"] == 2
        assert len(lines) == 0

    """
    # non-deterministic test, but a good example to keep for now
    def test_average_what_the(self):
        path = CsvPath()
        path.parse(
            f""
            ${NUMBERS}[1*]
            [
                @ave = average.test.onmatch(#count3, "line")
                @r = random(0,1)
                @c = count()
                @c2 = count_scans()
                @c3 = count_lines()
                @r == 1
                yes()
                print(count_lines()==1, "match, scan, line, random, average")
                print(yes(), "$.variables.c, $.variables.c2, $.variables.c3, $.variables.r, $.variables.ave")
            ]""
        )
        print("")
        lines = path.collect()
        print(f"test_average_what_the: path vars: {path.variables}")
        #assert path.variables["the_average"] == 2
        #assert len(lines) == 0
        """

    def test_function_median(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_median = median(count(#lastname), "line")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["the_median"] == 3
        assert len(lines) == 0

    def test_function_random(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @r = random(0, 1)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["r"] == 1 or path.variables["r"] == 0
        assert len(lines) == 0

    def test_function_match_length(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][length(#lastname)==3]")
        lines = path.collect()
        print(f"test_function_match_length: lines: {len(lines)}")
        assert len(lines) == 7

    def test_function_not(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][not(length(#lastname)==3)]")
        lines = path.collect()
        print(f"test_function_not: lines: {len(lines)}")
        assert len(lines) == 2

    def test_function_now(self):
        path = CsvPath()
        # obviously this will break and need updating 1x a year
        path.parse(f'${PATH}[*][now("%Y") == "2024"]')
        lines = path.collect()
        print(f"test_function_now: lines: {len(lines)}")
        assert len(lines) == 9

    def test_function_in(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][in( #0 , "Bug|Bird|Ants" )]')
        lines = path.collect()
        print(f"test_function_in: lines: {len(lines)}")
        assert len(lines) == 3

    def test_function_concat(self):
        path = CsvPath()
        path.parse(
            f"""
                        ${PATH}[*]
                               [ #0 == concat("B" , "ird") ]
                   """
        )
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
        assert len(lines) == 1

    def test_function_count_existance(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                exists(#lastname)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 9

    def test_function_increment(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = increment.test(yes(), 3)
                @j = increment.double_check(yes(), 2)
                @k = increment.rand(random(0,1)==1, 2)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["test"] == 9
        assert path.variables["i"] == 3
        assert path.variables["j"] == 4
        assert path.variables["double_check_increment"] == 4

    def test_function_increment2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = increment.never.onmatch(yes(), 3)
                @j = increment.always(yes(), 3)
                @k = increment.onmatch.still_never(yes(), 3)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 0
        assert path.variables["j"] == 3
        assert path.variables["i"] == 0
        assert path.variables["k"] == 0
        assert path.variables.get("still_never") is None

    def test_function_column(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = column("firstname")
                @j = column("lastname")
                @n = column(2)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["j"] == 1
        assert path.variables["i"] == 0
        assert path.variables["n"] == "say"

    def test_function_substring(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = substring("testtest", 4)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_substring: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["i"] == "test"

    def test_function_stop(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = concat( #firstname, #lastname)
                @c = count_lines()
                stop(@i == "FishBat")
                yes()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_stop: path vars: {path.variables}")
        print(f"test_function_stop: lines: {lines}")
        assert path.stopped is True
        assert len(lines) == 3
        assert path.variables["i"] == "FishBat"
        assert path.variables["c"] == 2

    def test_function_any_function1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
                @frog = any(header(), "Frog")
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["frog"] is True

    def test_function_any_function2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
                @found = any()
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["found"] is True

    def test_function_any_function3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
                @v = any(variable())
                @frog = any(header(), "Frog")
                @found = any()
                @slug = any("slug")
                @bear = any(header(),"Bear")
                @me = any("True")
                @h = any(header())
                @v2 = any(variable())
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["frog"] is True
        assert path.variables["found"] is True
        assert path.variables["slug"] is False
        assert path.variables["bear"] is False
        assert path.variables["v"] is False
        assert path.variables["v2"] is True
        assert path.variables["h"] is True

    def test_function_any_function4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[1-2]
            [
                @found = any(header())
                @notfound = not(any(header()))
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["notfound"] is True

    def test_function_any_function5(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1-2]
            [
                @found = any.onmatch(header())
                @found2 = any(header())
                @notfound = not(any.onmatch(header()))
                no()
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        # assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["found2"] is True
        assert path.variables["notfound"] is True

    def test_function_last1(self):
        path = CsvPath()
        matchpart = """
            [
                count_lines()==0 -> @first = 0
                last() -> @last = count_lines()
            ]"""

        matcher = Matcher(
            csvpath=path,
            data=matchpart,
            line=["Frog", "Bats", "ribbit..."],
            headers=["firstname", "lastname", "say"],
        )
        print("")
        count_lines = matcher.expressions[0][0].children[0].left.left.matches(skip=[])
        assert count_lines is True
        lines = matcher.expressions[0][0].children[0].left.left.to_value(skip=[])
        assert lines == 0
        is0 = matcher.expressions[0][0].children[0].left.matches(skip=[])
        assert is0 is True
        op = matcher.expressions[0][0].children[0].op
        assert op == "->"
        b1 = matcher.expressions[0][0].matches(skip=[])
        b2 = matcher.expressions[1][0].matches(skip=[])
        print("")
        print(f"test_function_last1: path vars: {path.variables}")
        print(f"test_function_last1: b1: {b1}, b2: {b2}")
        assert path.variables["first"] == 0
        assert b1 is True
        assert b2 is False

    def test_function_last2(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                count_lines()==0 -> @first = 0
                last() -> @last = count_lines()
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_last: path vars: {path.variables}")
        print(f"test_function_last: lines: {lines}")
        assert path.variables["last"] == 8
        assert path.variables["first"] == 0

    # FIXME: this is not really a deterministic test.
    def test_function_last3(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [ yes() -> print("$.line_count")
                last() -> print("the last row is $.line_count")
            ]
            """
        )
        print("")
        path.fast_forward()
        print(f"test_function_last: path vars: {path.variables}")

    def test_function_mod1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @mod = mod(count_lines(), 2)
                @mod == 0.0
                print.onmatch("$.variables.mod")
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_last: path vars: {path.variables}")
        print(f"test_function_last: lines: {lines}")
        assert path.variables["mod"] == 0.0
        assert len(lines) == 5

    # @mod3 = @mod == @mod2

    # FIXME: this works to show that @var.onchange correctly matches when set to a
    # new value. it is not a deterministic test. there is a deterministic test in test_function_onchange2
    # leaving this as an example, for now.
    def test_function_onchange1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                increment.test( yes(), 3)
                @oc.onchange = @test_increment
                print.onmatch("printing: oc: $.variables.oc, test: $.variables.test, count: $.match_count")
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_last: path vars: {path.variables}")
        print(f"test_function_last: lines: {lines}")
        assert path.variables["oc"] == 3.0
        assert len(lines) == 3

    def test_function_onchange2(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @oc.onchange = in(#firstname, "Frog|Bug|Fish")
                print.onmatch("printing: oc: $.variables.oc, count: $.match_count")
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_last: path vars: {path.variables}")
        print(f"test_function_last: lines: {lines}")
        assert path.variables["oc"] is True
        assert len(lines) == 4

    def test_exp_util_quals(self):
        name, quals = ExpressionUtility.get_name_and_qualifiers("test.onmatch")
        assert name == "test"
        assert "onmatch" in quals
        name, quals = ExpressionUtility.get_name_and_qualifiers("test.onchange.onmatch")
        assert name == "test"
        assert "onmatch" in quals
        assert "onchange" in quals
        name, quals = ExpressionUtility.get_name_and_qualifiers(
            "test.mytest.onchange.onmatch"
        )
        assert name == "test"
        assert "mytest" in quals
        assert "onmatch" in quals
        assert "onchange" in quals
