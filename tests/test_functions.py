import unittest
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


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
        path.parse(f'${PATH}[*][@p=percent("line")  above(@p,.35) #lastname=="Bat"]')
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
        path.parse(f'${PATH}[*][ #firstname=="David" @david=count_lines() ]')
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
                count(#firstname=="Frog")==1
                @say=#say
                @line=count_lines()
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
                @say=#say
                @line=count_lines()

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

    def test_function_add(self):
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

    def test_function_every(self):
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
        print(f"test_function_count_in: path vars: {path.variables}")
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

    def test_function_isinstance(self):
        path = CsvPath()
        print("checking ints")
        path.parse(f'${PATH}[*][ isinstance(count(), "int") ]')
        lines = path.collect()
        assert len(lines) == 9
        print(f"test_function_isinstance: lines: {lines}")
        print("checking dates")
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("11-23-2024", "datetime") ]')
        lines = path.collect()
        assert len(lines) == 9
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("2024-11-23", "datetime") ]')
        lines = path.collect()
        assert len(lines) == 9
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("2024-1-3", "datetime") ]')
        lines = path.collect()
        assert len(lines) == 9
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("2024-59-23", "datetime") ]')
        lines = path.collect()
        assert len(lines) == 0
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("1000-1-1", "datetime") ]')
        lines = path.collect()
        assert len(lines) == 9
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("1/12/2024", "datetime") ]')
        lines = path.collect()
        assert len(lines) == 9
        print("checking $$$")
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("$1000.59", "usd") ]')
        lines = path.collect()
        assert len(lines) == 9
        print("checking float")
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("11.59", "float") ]')
        lines = path.collect()
        assert len(lines) == 9
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("11.59", "int") ]')
        lines = path.collect()
        assert len(lines) == 0
        path = CsvPath()
        path.parse(f'${PATH}[*][ isinstance("11.59", "usd") ]')
        lines = path.collect()
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
        path.parse(f'${PATH}[*][ #0 == concat("B" , "ird") ]')
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
        assert len(lines) == 1

    def test_function_count_existance(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                #lastname
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 9
