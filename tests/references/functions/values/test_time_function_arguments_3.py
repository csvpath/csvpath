#
# time functions that take an argument (compendium 6.27g; NRE "Date and
# time functions", lines 88-150 and 568): a component of a given moment
# (':day_name(:date("2026-09-04"))' is Friday), an explicit component value
# (':year(2025)', ':hour_24(18)'), and a day relative to a moment
# (':yesterday(:date("2026-01-02"))', ':yesterday(:hour_24(18))'). Every one
# raised "does not take an argument" until the name_one gap review
# (2026-11-19, item F).
#
# The clock is pinned to Sunday 2026-01-04 12:30 UTC.
#
import os
from datetime import datetime, timezone

import pytest

from csvpath import CsvPaths
from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.selectors.date_3 import Date3
from csvpath.references.functions.values.clock_utility import ClockUtility as clut
from csvpath.references.functions.values.day_3 import Day3
from csvpath.references.functions.values.day_name_3 import DayName3
from csvpath.references.functions.values.hour_24_3 import Hour243
from csvpath.references.functions.values.hour_3 import Hour3
from csvpath.references.functions.values.minute_3 import Minute3
from csvpath.references.functions.values.month_3 import Month3
from csvpath.references.functions.values.month_name_3 import MonthName3
from csvpath.references.functions.values.now_3 import Now3
from csvpath.references.functions.values.second_3 import Second3
from csvpath.references.functions.values.today_3 import Today3
from csvpath.references.functions.values.year_3 import Year3
from csvpath.references.functions.values.yesterday_3 import Yesterday3
from csvpath.references.reference_exceptions_3 import (
    ReferenceException3,
    ReferenceRuntimeException3,
)
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.util.date_util import DateUtility as daut
from tests.references.cost.test_results_estimate_soundness_3 import CORPUS_CONFIG

PINNED = datetime(2026, 1, 4, 12, 30, 15, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def pinned_now(monkeypatch):
    monkeypatch.setattr(daut, "now", classmethod(lambda cls: PINNED))


def _valid(function: Function3) -> Function3:
    function.check_valid()
    return function


def _window(function: Function3) -> tuple:
    return (function.start_datetime().isoformat(), function.end_datetime().isoformat())


def _date(value: str) -> Date3:
    return _valid(Date3(arg=value))


# ===================
# ClockUtility, the shared part
# ===================


class TestClockUtility:
    def test_no_argument_is_now(self):
        assert clut.base(function=Year3()) == datetime(2026, 1, 4, 12, 30, 15)

    def test_a_time_function_argument_is_its_first_moment(self):
        assert clut.base(function=Year3(arg=_date("2025-03-04"))) == datetime(
            2025, 3, 4
        )

    def test_now_as_an_argument_is_now(self):
        assert clut.base(function=Minute3(arg=Now3())) == datetime(
            2026, 1, 4, 12, 30, 15
        )

    def test_an_int_sets_the_component(self):
        assert clut.base(function=Year3(arg=2024), component="year") == datetime(
            2024, 1, 1, 12, 30, 15
        )

    def test_an_int_without_a_component_raises(self):
        with pytest.raises(ReferenceException3, match="not an int"):
            clut.base(function=DayName3(arg=3))

    def test_an_impossible_component_raises(self):
        with pytest.raises(ReferenceException3, match="not a valid month"):
            clut.base(function=Month3(arg=13), component="month")

    def test_true_is_not_an_int(self):
        with pytest.raises(ReferenceException3):
            clut.base(function=Year3(arg=True), component="year")

    def test_moment_needs_a_time_function(self):
        with pytest.raises(ValueError):
            clut.moment(function=None)
        with pytest.raises(TypeError):
            clut.moment(function="2026-01-01")

    def test_base_needs_a_function(self):
        with pytest.raises(ValueError):
            clut.base(function=None)


# ===================
# a component of a given moment
# ===================


class TestComponentOfAMoment:
    @pytest.mark.parametrize(
        "function,value",
        [
            (Year3(arg=Date3(arg="2025-03-04")), 2025),
            (Month3(arg=Date3(arg="2025-03-04")), 3),
            (Day3(arg=Date3(arg="2025-03-04")), 4),
            (Hour243(arg=Date3(arg="2026-01-01_15-04-05")), 15),
            (Hour3(arg=Date3(arg="2026-01-01_15-04-05")), 3),
            (Minute3(arg=Date3(arg="2026-01-01_15-04-05")), 4),
            (Second3(arg=Date3(arg="2026-01-01_15-04-05")), 5),
            # NRE 141: Friday
            (DayName3(arg=Date3(arg="2026-09-04")), "Friday"),
            (MonthName3(arg=Date3(arg="2026-06-01")), "June"),
            # NRE 133, 137, 149, relative to the pinned clock
            (DayName3(arg=Yesterday3()), "Saturday"),
            (DayName3(arg=Today3()), "Sunday"),
            (Minute3(arg=Now3()), 30),
            # 6.27g
            (Year3(arg=Date3(arg="2026-01-01")), 2026),
        ],
    )
    def test_value(self, function, value):
        assert _valid(function).compute() == value

    def test_the_window_is_the_moments_period(self):
        assert _window(_valid(Year3(arg=_date("2025-03-04")))) == (
            "2025-01-01T00:00:00",
            "2025-12-31T23:59:59.999999",
        )
        assert _window(_valid(Month3(arg=_date("2024-02-10")))) == (
            "2024-02-01T00:00:00",
            "2024-02-29T23:59:59.999999",
        )
        assert _window(_valid(Hour243(arg=_date("2026-01-01_15-04-05")))) == (
            "2026-01-01T15:00:00",
            "2026-01-01T15:59:59.999999",
        )


# ===================
# an explicit component
# ===================


class TestExplicitComponent:
    @pytest.mark.parametrize(
        "function,value,window",
        [
            (
                Year3(arg=2024),
                2024,
                ("2024-01-01T00:00:00", "2024-12-31T23:59:59.999999"),
            ),
            (Month3(arg=6), 6, ("2026-06-01T00:00:00", "2026-06-30T23:59:59.999999")),
            (Day3(arg=2), 2, ("2026-01-02T00:00:00", "2026-01-02T23:59:59.999999")),
            (
                Hour243(arg=18),
                18,
                ("2026-01-04T18:00:00", "2026-01-04T18:59:59.999999"),
            ),
            (Minute3(arg=5), 5, ("2026-01-04T12:05:00", "2026-01-04T12:05:59.999999")),
            (Second3(arg=9), 9, ("2026-01-04T12:30:09", "2026-01-04T12:30:09.999999")),
        ],
    )
    def test_value_and_window(self, function, value, window):
        assert _valid(function).compute() == value
        assert _window(function) == window

    @pytest.mark.parametrize(
        "function",
        [Month3(arg=13), Month3(arg=0), Day3(arg=32), Hour243(arg=24), Minute3(arg=60)],
    )
    def test_an_impossible_value_raises_when_built(self, function):
        with pytest.raises(ReferenceException3, match="is not a valid"):
            function.check_valid()

    @pytest.mark.parametrize("hour", [1, 6, 12, "6"])
    def test_a_12_hour_value_is_ambiguous(self, hour):
        # the 12-hour clock: ':hour(6)' cannot say am or pm
        with pytest.raises(
            ReferenceException3,
            match=r"ambiguous.*Use :hour_24\(\d+\) or :hour_24\(\d+\)",
        ):
            Hour3(arg=hour).check_valid()

    @pytest.mark.parametrize("hour", [0, 13, 18, 23, "18"])
    def test_a_24_hour_value_is_not_an_hour(self, hour):
        # ':hour()' is the 12-hour clock; ':hour_24(n)' sets an hour (D40 h)
        with pytest.raises(
            ReferenceException3, match=r"does not set an hour.*Use :hour_24\(\d+\)"
        ):
            Hour3(arg=hour).check_valid()

    @pytest.mark.parametrize(
        "hour,start", [(18, "2026-01-04T18:00:00"), (0, "2026-01-04T00:00:00")]
    )
    def test_hour_24_sets_the_hour(self, hour, start):
        # NRE 568 ':yesterday(:hour_24(18))'
        f = _valid(Hour243(arg=hour))
        assert f.start_datetime().isoformat() == start
        assert f.compute() == hour

    @pytest.mark.parametrize(
        "function,value",
        [(Year3(arg="2025"), 2025), (Month3(arg=" 6 "), 6), (Hour243(arg="18"), 18)],
    )
    def test_a_string_of_digits_is_the_number(self, function, value):
        # an @variable taken from data is a string (NRE 102 ':year(@the_year)')
        assert _valid(function).compute() == value

    def test_a_string_that_is_not_a_number_raises(self):
        with pytest.raises(
            ReferenceException3, match="a whole number written in digits"
        ):
            Year3(arg="last year").check_valid()


class TestCalendarEdges:
    # an int component used to carry today's day into another month or year
    # (reviewer on #788)
    @pytest.mark.parametrize(
        "today,function,window",
        [
            (
                datetime(2026, 1, 30, 9, tzinfo=timezone.utc),
                Month3(arg=2),
                ("2026-02-01T00:00:00", "2026-02-28T23:59:59.999999"),
            ),
            (
                datetime(2026, 3, 31, 9, tzinfo=timezone.utc),
                Month3(arg=6),
                ("2026-06-01T00:00:00", "2026-06-30T23:59:59.999999"),
            ),
            (
                datetime(2028, 2, 29, 9, tzinfo=timezone.utc),
                Year3(arg=2025),
                ("2025-01-01T00:00:00", "2025-12-31T23:59:59.999999"),
            ),
            (
                datetime(2028, 2, 29, 9, tzinfo=timezone.utc),
                Year3(arg=2027),
                ("2027-01-01T00:00:00", "2027-12-31T23:59:59.999999"),
            ),
        ],
    )
    def test_a_month_or_year_from_a_month_end(
        self, monkeypatch, today, function, window
    ):
        monkeypatch.setattr(daut, "now", classmethod(lambda cls: today))
        assert _window(_valid(function)) == window

    def test_a_day_that_this_month_lacks_raises_and_names_the_month(self, monkeypatch):
        monkeypatch.setattr(
            daut,
            "now",
            classmethod(lambda cls: datetime(2026, 4, 10, tzinfo=timezone.utc)),
        )
        with pytest.raises(ReferenceException3, match="not a valid day in April 2026"):
            Day3(arg=31).check_valid()

    @pytest.mark.parametrize(
        "date,yesterday",
        [
            ("2024-03-01", "2024-02-29"),
            ("2026-01-01", "2025-12-31"),
            ("2026-03-01", "2026-02-28"),
        ],
    )
    def test_yesterday_across_a_month_or_year(self, date, yesterday):
        assert _valid(Yesterday3(arg=_date(date))).compute() == yesterday

    @pytest.mark.parametrize("function", [DayName3(arg=3), MonthName3(arg=6)])
    def test_a_name_takes_no_int(self, function):
        with pytest.raises(ReferenceException3, match="argument must be one of"):
            function.check_valid()


# ===================
# a day relative to a moment
# ===================


class TestRelativeDay:
    def test_yesterday_of_a_date(self):
        # 6.27g's own example
        f = _valid(Yesterday3(arg=_date("2026-01-02")))
        assert f.compute() == "2026-01-01"
        assert _window(f) == ("2026-01-01T00:00:00", "2026-01-01T23:59:59.999999")

    def test_yesterday_of_an_hour_starts_at_that_hour(self):
        # NRE 568, "since close of business yesterday": from 18:00 to the
        # end of yesterday
        f = _valid(Yesterday3(arg=_valid(Hour243(arg=18))))
        assert f.compute() == "2026-01-03"
        assert _window(f) == ("2026-01-03T18:00:00", "2026-01-03T23:59:59.999999")

    def test_yesterday_of_a_time_of_day_runs_to_the_end_of_the_day(self):
        # a one-second ':date()' does not make yesterday one second long
        f = _valid(Yesterday3(arg=_date("2026-01-02_10-00-00")))
        assert _window(f) == ("2026-01-01T10:00:00", "2026-01-01T23:59:59.999999")

    def test_today_of_a_date_is_that_day(self):
        f = _valid(Today3(arg=_date("2025-07-04")))
        assert f.compute() == "2025-07-04"
        assert _window(f) == ("2025-07-04T00:00:00", "2025-07-04T23:59:59.999999")

    def test_now_as_the_argument_is_now_s_day(self):
        assert _window(_valid(Yesterday3(arg=Now3()))) == _window(_valid(Yesterday3()))
        assert _window(_valid(Today3(arg=Now3()))) == _window(_valid(Today3()))

    def test_a_format_string_formats_the_date(self):
        assert _valid(Yesterday3(arg="%A")).compute() == "Saturday"
        assert _valid(Today3(arg="%Y%m%d")).compute() == "20260104"
        # the window stays the day
        assert _window(_valid(Yesterday3(arg="%A"))) == _window(_valid(Yesterday3()))

    def test_a_date_string_raises_and_says_use_date(self):
        with pytest.raises(ReferenceException3, match=":date\\("):
            Yesterday3(arg="2026-01-02").check_valid()

    @pytest.mark.parametrize("arg", [Year3(), Month3(arg=6)])
    def test_an_argument_coarser_than_a_day_raises(self, arg):
        with pytest.raises(ReferenceException3, match="no single day"):
            Yesterday3(arg=arg).check_valid()

    @pytest.mark.parametrize("arg", [5, True])
    def test_a_number_raises(self, arg):
        with pytest.raises(
            ReferenceException3, match="time function or a format string"
        ):
            Today3(arg=arg).check_valid()


class TestResolvedValues:
    # an @variable or "{...}" value is only known once resolved; the format
    # check runs again on it (reviewer on #788)
    def test_a_resolved_date_string_raises(self):
        f = _valid(Yesterday3(arg="%A"))
        f.arg = "2026-01-02"
        with pytest.raises(ReferenceRuntimeException3, match="format string"):
            f.compute()
        with pytest.raises(ReferenceRuntimeException3, match="format string"):
            f.start_datetime()

    @pytest.mark.parametrize(
        "value,message", [(6, "ambiguous"), (18, "does not set an hour")]
    )
    def test_a_resolved_number_raises(self, value, message):
        # an @variable resolves after check_valid(); base_datetime() checks it
        f = _valid(Hour3(arg=_date("2026-01-02")))
        f.arg = value
        with pytest.raises(ReferenceException3, match=message):
            f.start_datetime()


class TestTheArgumentTypeMessage:
    def test_it_names_what_is_allowed_in_words(self):
        with pytest.raises(ReferenceException3) as e:
            Year3(arg=DayName3()).check_valid()
        message = str(e.value)
        assert "an int" in message and "a time function" in message
        assert "got :day_name()" in message
        assert "<class" not in message

    def test_type_names(self):
        assert Function3._arg_type_name(str) == "a string"
        assert Function3._arg_type_name(int) == "an int"
        assert Function3._arg_type_name(Now3) == ":now()"
        with pytest.raises(ValueError):
            Function3._arg_type_name(None)


# ===================
# through a reference: the NRE's own forms parse, build and compute
# ===================


@pytest.fixture(scope="module")
def csvpaths():
    return CsvPaths()


def _built(csvpaths, reference: str) -> Function3:
    finder = ReferenceFinderFactory3.for_reference(
        reference=reference, csvpaths=csvpaths
    )
    return finder._build(finder.ref.parsed.name_three.functions[0])


class TestThroughAReference:
    @pytest.mark.parametrize(
        "reference,value",
        [
            ('$acme.files.*.:day_name(:date("2026-09-04"))', "Friday"),
            ("$acme.files.*.:day_name(:yesterday())", "Saturday"),
            ("$acme.files.*.:minute(:now())", 30),
            ('$acme.files.*.:yesterday(:date("2026-01-02"))', "2026-01-01"),
            ("$acme.files.*.:year(2025)", 2025),
        ],
    )
    def test_value(self, csvpaths, reference, value):
        assert _built(csvpaths, reference).compute() == value

    @pytest.mark.parametrize("direction", ["from", "to", "before", "after"])
    def test_close_of_business_as_an_anchor(self, csvpaths, direction):
        # NRE 568 as written, with each direction (6.27b: the first moment)
        built = _built(
            csvpaths, f"$acme.files.*.:{direction}(:yesterday(:hour_24(18)))"
        )
        assert built.arg.start_datetime() == datetime(2026, 1, 3, 18, 0)

    def test_a_variable_year(self, csvpaths):
        # NRE 102 ':year(@the_year)', from data as a string or as an int
        for value in ("2025", 2025):
            finder = ReferenceFinderFactory3.for_reference(
                reference="$acme.files.*.:year(@the_year)", csvpaths=csvpaths
            )
            finder.set_variable("the_year", value=value)
            assert (
                finder._build(finder.ref.parsed.name_three.functions[0]).compute()
                == 2025
            )

    @pytest.mark.parametrize(
        "reference",
        [
            "$acme.files.*.:yesterday(@d)",
            '$acme.files.*.:yesterday("{@d}")',
            '$acme.files.*.:today("{@d}")',
        ],
    )
    def test_a_variable_date_where_a_format_goes_raises(self, csvpaths, reference):
        finder = ReferenceFinderFactory3.for_reference(
            reference=reference, csvpaths=csvpaths
        )
        finder.set_variable("d", value="2026-01-02")
        # when the argument resolves, before any reads
        with pytest.raises(ReferenceRuntimeException3, match="format string"):
            finder._build(finder.ref.parsed.name_three.functions[0])

    @pytest.mark.parametrize(
        "reference,segment",
        [
            ("$acme.files.orders/:year(2026)", "2026"),
            ('$acme.files.orders/:year(:date("2025-03-03"))', "2025"),
            ('$acme.files.orders/:name("{:year(2025)}.csv")', "2025.csv"),
        ],
    )
    def test_a_path_segment(self, csvpaths, reference, segment):
        finder = ReferenceFinderFactory3.for_reference(
            reference=reference, csvpaths=csvpaths
        )
        assert (
            finder._compile_path_pattern(finder.ref.parsed.name_one.path)[-1] == segment
        )

    def test_an_interpolated_name(self, csvpaths):
        # NRE 83
        finder = ReferenceFinderFactory3.for_reference(
            reference='$acme.files.orders/:name("Summary for {:day_name(:yesterday())}.xlsx")',
            csvpaths=csvpaths,
        )
        name = finder._build(finder.ref.parsed.name_one.path[1])
        assert name.arg == "Summary for Saturday.xlsx"


@pytest.fixture(scope="module")
def corpus():
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = os.path.abspath(CORPUS_CONFIG)
    try:
        yield CsvPaths()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


class TestCsvpaths:
    # its "no filtering mechanism" guard is for field accessors; it raised
    # for a time function's argument too. The corpus groups were loaded in
    # 2026, the pinned clock's year.
    @pytest.mark.parametrize(
        "reference,count",
        [
            ("$validate_orders.csvpaths.:year(:today()):last()", 1),
            ("$validate_orders.csvpaths.:year(2026):last()", 1),
            ("$validate_orders.csvpaths.:year(2020):last()", 0),
            ('$validate_orders.csvpaths.:year(:date("2020-06-01")):last()', 0),
        ],
    )
    def test_query(self, corpus, reference, count):
        finder = ReferenceFinderFactory3.for_reference(
            reference=reference, csvpaths=corpus
        )
        assert len(finder.query().results) == count


# ===================
# the estimate with @variables set: a bad value raises at build, so the
# estimate predicts what query does (reviewer on #788, round 2)
# ===================

VARIABLES = {
    "y": 2026,
    "bad": "abc",
    "h6": 6,
    "h18": 18,
    "d": "2026-08-15",
    "fmt": "%A",
}

VARIABLE_SHAPES = [
    "$validate_orders.results.:flatten():year(@y).*",
    "$validate_orders.results.:flatten():from(:year(@y)).*",
    "$validate_orders.results.:flatten():year(@bad).*",
    "$validate_orders.results.:flatten():hour(@h6).*",
    "$validate_orders.results.:flatten():from(:yesterday(:hour(@h18))).*",
    "$validate_orders.results.:flatten():from(:yesterday(:hour_24(@h18))).*",
    "$validate_orders.results.:flatten():yesterday(@d).*",
    '$validate_orders.results.:flatten():yesterday("{@d}").*',
    "$validate_orders.results.:flatten():yesterday(@fmt).*",
    "$validate_orders.results.:flatten():year(@unset).*",
    "$orders.files.:flatten().:year(@bad)",
    "$orders.files.:flatten().:yesterday(@d)",
    "$validate_orders.csvpaths.:yesterday(@d)",
    "$validate_orders.csvpaths.:year(@bad)",
]


def _with_variables(corpus, reference: str):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
    for name, value in VARIABLES.items():
        finder.set_variable(name, value=value)
    return finder


@pytest.mark.parametrize("reference", VARIABLE_SHAPES)
def test_the_estimate_keeps_its_contract_with_variables(corpus, reference):
    from csvpath.references.reference_estimate_3 import QUERY, RESOLVE
    from tests.references.cost.read_counter import ReadCounter
    from tests.references.cost.test_results_estimate_soundness_3 import _problems

    est = _with_variables(corpus, reference).estimate()
    finder = _with_variables(corpus, reference)
    raised = None
    resolve_reads = {}
    with ReadCounter.for_csvpaths(corpus) as query:
        try:
            selection = finder.query()
        except Exception as e:
            raised = e
    if raised is None:
        with ReadCounter.for_csvpaths(corpus) as resolve:
            try:
                finder.resolve_from(selection)
            except Exception as e:
                raised = e
        resolve_reads = dict(resolve.reads)
    measured = {QUERY: dict(query.reads), RESOLVE: resolve_reads}
    assert _problems(est, measured, raised) == []


@pytest.mark.parametrize(
    "reference,message",
    [
        ("$acme.files.*.:year(@bad)", "a whole number"),
        ("$acme.files.*.:hour(@h6)", "ambiguous"),
        ("$acme.files.*.:hour(@h18)", "does not set an hour"),
        ("$acme.files.*.:yesterday(@d)", "format string"),
    ],
)
def test_a_bad_variable_value_raises_when_built(csvpaths, reference, message):
    finder = ReferenceFinderFactory3.for_reference(
        reference=reference, csvpaths=csvpaths
    )
    for name, value in VARIABLES.items():
        finder.set_variable(name, value=value)
    with pytest.raises(ReferenceRuntimeException3, match=message):
        finder._build(finder.ref.parsed.name_three.functions[0])
