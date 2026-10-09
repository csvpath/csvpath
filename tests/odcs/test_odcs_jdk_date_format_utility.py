import datetime

import pytest

from csvpath.odcs.jdk_date_format_utility import JdkDateFormatUtility as jdut


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("yyyy-MM-dd", "%Y-%m-%d"),
        ("dd/MM/yyyy", "%d/%m/%Y"),
        ("yy", "%y"),
        ("uuuu", "%Y"),
        ("MMM d, yyyy", "%b %d, %Y"),
        ("MMMM", "%B"),
        ("EEE", "%a"),
        ("EEEE", "%A"),
        ("DDD", "%j"),
        ("hh:mm a", "%I:%M %p"),
        ("HH:mm:ss", "%H:%M:%S"),
        ("HH:mm:ss.SSS", "%H:%M:%S.%f"),
        ("yyyy-MM-dd'T'HH:mm:ss.SSS", "%Y-%m-%dT%H:%M:%S.%f"),
        ("yyyy-MM-ddTHH:mm:ssZ", "%Y-%m-%dT%H:%M:%S%z"),
        ("yyyy-MM-dd'T'HH:mm:ssXXX", "%Y-%m-%dT%H:%M:%S%z"),
        ("HH:mm z", "%H:%M %Z"),
        ("'at' HH 'o''clock'", "at %H o'clock"),
        ("''HH''", "'%H'"),
        ("100%", "100%%"),
    ],
)
def test_odcs_jdut_to_strftime(pattern: str, expected: str) -> None:
    assert jdut.to_strftime(pattern=pattern) == expected


@pytest.mark.parametrize("pattern", ["G yyyy", "QQ", "ww", "yyyy[-MM]", "K:mm"])
def test_odcs_jdut_to_strftime_unsupported(pattern: str) -> None:
    with pytest.raises(ValueError):
        jdut.to_strftime(pattern=pattern)


def test_odcs_jdut_to_strftime_unterminated_quote() -> None:
    with pytest.raises(ValueError):
        jdut.to_strftime(pattern="yyyy 'at")


def test_odcs_jdut_to_strftime_bad_input() -> None:
    with pytest.raises(ValueError):
        jdut.to_strftime(pattern=None)
    with pytest.raises(ValueError):
        jdut.to_strftime(pattern=" ")
    with pytest.raises(TypeError):
        jdut.to_strftime(pattern=5)


def test_odcs_jdut_translations_parse_real_values() -> None:
    #
    # the translated formats must actually parse values written in the
    # original JDK pattern
    #
    cases = [
        ("dd/MM/yyyy", "15/06/2025"),
        ("yyyy-MM-dd'T'HH:mm:ss.SSS", "2025-06-15T10:30:00.123"),
        ("yyyy-MM-ddTHH:mm:ssZ", "2025-06-15T11:00:00Z"),
        ("yyyy-MM-ddTHH:mm:ssZ", "2025-06-15T11:00:00+10:00"),
        ("MMM d, yyyy", "Jun 5, 2025"),
    ]
    for pattern, value in cases:
        datetime.datetime.strptime(value, jdut.to_strftime(pattern=pattern))


def test_odcs_jdut_parsing_format() -> None:
    formats = ["%d/%m/%Y", jdut.ISO_DATE]
    assert jdut.parsing_format(value="01/01/2030", formats=formats) == "%d/%m/%Y"
    assert jdut.parsing_format(value="2020-01-01", formats=formats) == jdut.ISO_DATE
    assert jdut.parsing_format(value="Jan 1 2020", formats=formats) is None


def test_odcs_jdut_parsing_format_bad_input() -> None:
    with pytest.raises(TypeError):
        jdut.parsing_format(value=20200101, formats=[jdut.ISO_DATE])
    with pytest.raises(ValueError):
        jdut.parsing_format(value="2020-01-01", formats=[])
