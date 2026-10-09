"""PropertyConverter, one rule at a time. Each test converts a single
property and checks the resulting CsvPathParts and report directly."""

import pytest

from csvpath.odcs.conversion_report import ConversionReport
from csvpath.odcs.csvpath_parts import CsvPathParts
from csvpath.odcs.property_converter import PropertyConverter


def _convert(prop: dict, index: int = 0) -> tuple[CsvPathParts, ConversionReport]:
    parts = CsvPathParts()
    report = ConversionReport()
    PropertyConverter(
        obj="t", prop=prop, index=index, parts=parts, report=report
    ).convert()
    return parts, report


def _features(report: ConversionReport) -> list[tuple[str, str]]:
    return [(s.location, s.feature) for s in report.skipped]


# ============================
# constructor
# ============================


def test_odcs_property_converter_bad_input() -> None:
    parts = CsvPathParts()
    report = ConversionReport()
    with pytest.raises(ValueError):
        PropertyConverter(
            obj="", prop={"name": "a"}, index=0, parts=parts, report=report
        )
    with pytest.raises(TypeError):
        PropertyConverter(obj="t", prop=None, index=0, parts=parts, report=report)
    with pytest.raises(ValueError):
        PropertyConverter(
            obj="t", prop={"name": ""}, index=0, parts=parts, report=report
        )
    with pytest.raises(TypeError):
        PropertyConverter(
            obj="t", prop={"name": "a"}, index=0, parts=None, report=report
        )
    with pytest.raises(TypeError):
        PropertyConverter(
            obj="t", prop={"name": "a"}, index=0, parts=parts, report=None
        )


# ============================
# names and qualifiers
# ============================


def test_odcs_property_physical_name_is_the_header() -> None:
    parts, _ = _convert({"name": "customer_id", "physicalName": "cust_id"})
    assert parts.line_args == ["string(#cust_id)"]


def test_odcs_property_header_needing_quotes_or_index() -> None:
    parts, _ = _convert({"name": "Order ID"})
    assert parts.line_args == ['string(#"Order ID")']
    parts, _ = _convert({"name": "price($)"}, index=4)
    assert parts.line_args == ["string(#4)"]


def test_odcs_property_no_logical_type_is_string() -> None:
    parts, report = _convert({"name": "a", "required": True, "unique": True})
    assert parts.line_args == ["string.notnone.distinct(#a)"]
    assert report.skipped == []


# ============================
# string
# ============================


def test_odcs_property_string_lengths() -> None:
    opts = {"logicalType": "string"}
    parts, _ = _convert({"name": "a", **opts, "logicalTypeOptions": {"maxLength": 5}})
    assert parts.line_args == ["string(#a, 5)"]
    parts, _ = _convert({"name": "a", **opts, "logicalTypeOptions": {"minLength": 2}})
    assert parts.line_args == ["string(#a, none(), 2)"]
    parts, _ = _convert(
        {"name": "a", **opts, "logicalTypeOptions": {"maxLength": 5, "minLength": 2}}
    )
    assert parts.line_args == ["string(#a, 5, 2)"]


@pytest.mark.parametrize(
    "fmt,fn", [("email", "email"), ("uuid", "uuid"), ("uri", "url")]
)
def test_odcs_property_string_formats(fmt: str, fn: str) -> None:
    parts, report = _convert(
        {
            "name": "a",
            "logicalType": "string",
            "required": True,
            "logicalTypeOptions": {"format": fmt},
        }
    )
    assert parts.line_args == [f"{fn}.notnone(#a)"]
    assert report.skipped == []


def test_odcs_property_string_format_drops_length() -> None:
    parts, report = _convert(
        {
            "name": "a",
            "logicalType": "string",
            "logicalTypeOptions": {"format": "email", "maxLength": 50},
        }
    )
    assert parts.line_args == ["email(#a)"]
    assert _features(report) == [
        ("properties.a.logicalTypeOptions.maxLength", "maxLength")
    ]


def test_odcs_property_string_unsupported_format() -> None:
    parts, report = _convert(
        {"name": "a", "logicalType": "string", "logicalTypeOptions": {"format": "ipv6"}}
    )
    assert parts.line_args == ["string(#a)"]
    assert _features(report) == [
        ("properties.a.logicalTypeOptions.format", "format.ipv6")
    ]


def test_odcs_property_string_pattern() -> None:
    prop = {
        "name": "a",
        "logicalType": "string",
        "logicalTypeOptions": {"pattern": "^x/y$"},
    }
    parts, _ = _convert(prop)
    assert parts.line_checks == [r"or( empty(#a), regex(/^x\/y$/, #a) )"]
    parts, _ = _convert({**prop, "required": True})
    assert parts.line_checks == [r"regex(/^x\/y$/, #a)"]


def test_odcs_property_string_bad_pattern() -> None:
    parts, report = _convert(
        {
            "name": "a",
            "logicalType": "string",
            "logicalTypeOptions": {"pattern": "(?<n>x)"},
        }
    )
    assert parts.line_checks == []
    assert _features(report) == [("properties.a.logicalTypeOptions.pattern", "pattern")]


# ============================
# numbers
# ============================


def test_odcs_property_integer_bounds() -> None:
    parts, _ = _convert(
        {"name": "a", "logicalType": "integer", "logicalTypeOptions": {"minimum": 1}}
    )
    assert parts.line_args == ["integer(#a, none(), 1)"]


def test_odcs_property_number_exclusive_bounds() -> None:
    parts, _ = _convert(
        {
            "name": "a",
            "logicalType": "number",
            "logicalTypeOptions": {"exclusiveMinimum": 0, "exclusiveMaximum": 1.5},
        }
    )
    assert parts.line_args == ["decimal(#a)"]
    assert parts.line_checks == [
        "or( empty(#a), gt(#a, 0) )",
        "or( empty(#a), gt(1.5, #a) )",
    ]


def test_odcs_property_number_unsupported_option() -> None:
    _, report = _convert(
        {"name": "a", "logicalType": "integer", "logicalTypeOptions": {"format": "i32"}}
    )
    assert _features(report) == [("properties.a.logicalTypeOptions.format", "format")]


def test_odcs_property_multiple_of() -> None:
    prop = {
        "name": "a",
        "logicalType": "integer",
        "logicalTypeOptions": {"multipleOf": 5},
    }
    parts, report = _convert(prop)
    assert parts.line_checks == ["or( empty(#a), eq( mod(#a, 5), 0 ) )"]
    parts, _ = _convert({**prop, "required": True})
    assert parts.line_checks == ["eq( mod(#a, 5), 0 )"]
    parts, _ = _convert({**prop, "logicalTypeOptions": {"multipleOf": 5.0}})
    assert parts.line_checks == ["or( empty(#a), eq( mod(#a, 5), 0 ) )"]
    assert report.skipped == []


def test_odcs_property_multiple_of_non_integer_is_skipped() -> None:
    parts, report = _convert(
        {
            "name": "a",
            "logicalType": "number",
            "logicalTypeOptions": {"multipleOf": 0.5},
        }
    )
    assert parts.line_checks == []
    assert _features(report) == [
        ("properties.a.logicalTypeOptions.multipleOf", "multipleOf")
    ]


# ============================
# boolean
# ============================


def test_odcs_property_boolean_required() -> None:
    parts, _ = _convert({"name": "a", "logicalType": "boolean", "required": True})
    assert parts.line_args == ["boolean.notnone(#a)"]
    assert parts.line_checks == []


def test_odcs_property_boolean_optional_works_around_300_and_302() -> None:
    parts, report = _convert({"name": "a", "logicalType": "boolean", "unique": True})
    assert parts.line_args == ["blank(#a)"]
    assert parts.line_checks == [
        'or( empty(#a), in( lower( strip(#a) ), "true|false|1|0" ) )',
        "or( empty(#a), not( has_dups(#a) ) )",
    ]
    assert report.skipped == []


# ============================
# unique: empty values are never duplicates
# ============================


def test_odcs_property_unique_required_uses_distinct() -> None:
    parts, _ = _convert({"name": "a", "required": True, "unique": True})
    assert parts.line_args == ["string.notnone.distinct(#a)"]
    assert parts.line_checks == []


@pytest.mark.parametrize("lt", ["string", "integer", "number", "date", "timestamp"])
def test_odcs_property_unique_optional_ignores_empties(lt: str) -> None:
    parts, report = _convert({"name": "a", "logicalType": lt, "unique": True})
    assert ".distinct" not in parts.line_args[0]
    assert "or( empty(#a), not( has_dups(#a) ) )" in parts.line_checks
    assert report.skipped == []


# ============================
# dates
# ============================


def test_odcs_property_date_required() -> None:
    parts, _ = _convert(
        {
            "name": "a",
            "logicalType": "date",
            "required": True,
            "logicalTypeOptions": {"format": "dd/MM/yyyy"},
        }
    )
    assert parts.line_args == ['date.notnone(#a, "%d/%m/%Y")']


def test_odcs_property_date_optional_works_around_300() -> None:
    parts, _ = _convert({"name": "a", "logicalType": "date"})
    assert parts.line_args == ["blank(#a)"]
    assert parts.line_checks == ['or( empty(#a), date(#a, "%Y-%m-%d") )']


def test_odcs_property_timestamp_without_format_is_lenient() -> None:
    parts, _ = _convert({"name": "a", "logicalType": "timestamp", "required": True})
    assert parts.line_args == ["datetime.notnone(#a)"]


def test_odcs_property_time_default_format() -> None:
    parts, _ = _convert({"name": "a", "logicalType": "time", "required": True})
    assert parts.line_args == ['datetime.notnone(#a, "%H:%M:%S")']


def test_odcs_property_date_untranslatable_format() -> None:
    parts, report = _convert(
        {
            "name": "a",
            "logicalType": "timestamp",
            "required": True,
            "logicalTypeOptions": {"format": "G yyyy"},
        }
    )
    assert parts.line_args == ["datetime.notnone(#a)"]
    assert _features(report) == [("properties.a.logicalTypeOptions.format", "format")]


def test_odcs_property_date_bounds() -> None:
    parts, report = _convert(
        {
            "name": "a",
            "logicalType": "date",
            "required": True,
            "logicalTypeOptions": {
                "format": "dd/MM/yyyy",
                "minimum": "2020-01-01",
                "exclusiveMinimum": "31/12/2019",
                "maximum": "31/12/2030",
                "exclusiveMaximum": "2031-01-01",
            },
        }
    )
    f = 'date(#a, "%d/%m/%Y")'
    assert parts.line_checks == [
        f'gte( {f}, date("2020-01-01", "%Y-%m-%d") )',
        f'gt( {f}, date("31/12/2019", "%d/%m/%Y") )',
        f'lte( {f}, date("31/12/2030", "%d/%m/%Y") )',
        f'gt( date("2031-01-01", "%Y-%m-%d"), {f} )',
    ]
    assert report.skipped == []


def test_odcs_property_date_bound_unparsable() -> None:
    parts, report = _convert(
        {
            "name": "a",
            "logicalType": "date",
            "logicalTypeOptions": {"minimum": "Jan 1 2020"},
        }
    )
    assert parts.line_checks == ['or( empty(#a), date(#a, "%Y-%m-%d") )']
    assert _features(report) == [("properties.a.logicalTypeOptions.minimum", "minimum")]


# ============================
# untyped
# ============================


@pytest.mark.parametrize("lt", ["array", "object", "map", "vector"])
def test_odcs_property_untyped(lt: str) -> None:
    parts, report = _convert({"name": "a", "logicalType": lt, "required": True})
    assert parts.line_args == ["blank(#a)"]
    assert _features(report) == [("properties.a", f"logicalType.{lt}")]
    assert "required and unique are not checked" in report.skipped[0].reason


# ============================
# allowed values
# ============================


def test_odcs_property_enum_v32_objects_and_plain_values() -> None:
    parts, _ = _convert(
        {"name": "a", "enum": [{"value": "x"}, {"value": "y", "label": "Y"}]}
    )
    assert parts.line_checks == ['or( empty(#a), in(#a, "x|y") )']
    parts, _ = _convert({"name": "a", "required": True, "enum": ["x", "y"]})
    assert parts.line_checks == ['in(#a, "x|y")']


def test_odcs_property_enum_inexpressible_value() -> None:
    parts, report = _convert({"name": "a", "enum": [{"value": "x|y"}]})
    assert parts.line_checks == []
    assert _features(report) == [("properties.a.enum", "enum")]


def _invalid_values(args: dict, **threshold) -> dict:
    rule = {"metric": "invalidValues", "arguments": args}
    rule.update(threshold or {"mustBe": 0})
    return {"name": "a", "quality": [rule]}


def test_odcs_property_invalid_values_zero_tolerance() -> None:
    parts, _ = _convert(_invalid_values({"validValues": ["x", "y"]}))
    assert parts.line_checks == ['or( empty(#a), in(#a, "x|y") )']
    assert parts.counters == [] and parts.last_checks == []


def test_odcs_property_invalid_values_pattern_and_values() -> None:
    parts, _ = _convert(_invalid_values({"validValues": ["x"], "pattern": "^x$"}))
    assert parts.line_checks == [
        'or( empty(#a), and( in(#a, "x"), regex(/^x$/, #a) ) )'
    ]


def test_odcs_property_invalid_values_threshold() -> None:
    parts, _ = _convert(_invalid_values({"validValues": ["x"]}, mustBeLessThan=5))
    assert parts.line_checks == ['or( empty(#a), in(#a, "x") )']
    assert parts.counters == [
        'not.nocontrib( or( empty(#a), in(#a, "x") ) ) -> counter.a_invalid(1)'
    ]
    assert parts.last_checks == [
        "and.nocontrib( eq( count_lines(), total_lines() ), gte( @a_invalid, 5 ) ) -> fail()"
    ]


def test_odcs_property_invalid_values_without_arguments() -> None:
    parts, report = _convert(_invalid_values({}))
    assert parts.line_checks == []
    assert _features(report) == [("properties.a.quality[0]", "quality.invalidValues")]


def test_odcs_property_invalid_values_bad_arguments() -> None:
    _, report = _convert(
        _invalid_values({"validValues": ["x|y"], "pattern": "(?<n>x)"})
    )
    assert _features(report) == [
        ("properties.a.quality[0].arguments.validValues", "validValues"),
        ("properties.a.quality[0].arguments.pattern", "pattern"),
    ]


# ============================
# other quality rules
# ============================


def test_odcs_property_null_values_zero_is_required() -> None:
    parts, _ = _convert(
        {"name": "a", "quality": [{"metric": "nullValues", "mustBe": 0}]}
    )
    assert parts.line_args == ["string.notnone(#a)"]
    assert parts.counters == []


def test_odcs_property_null_values_threshold() -> None:
    parts, _ = _convert(
        {"name": "a", "quality": [{"metric": "nullValues", "mustBeLessOrEqualTo": 2}]}
    )
    assert parts.line_args == ["string.notnone(#a)"]
    assert parts.counters == ["empty.nocontrib(#a) -> counter.a_null(1)"]
    assert parts.last_checks == [
        "and.nocontrib( eq( count_lines(), total_lines() ), gt( @a_null, 2 ) ) -> fail()"
    ]


def test_odcs_property_duplicate_values_zero() -> None:
    parts, report = _convert(
        {"name": "a", "quality": [{"metric": "duplicateValues", "mustBe": 0}]}
    )
    assert parts.line_args == ["string(#a)"]
    assert parts.line_checks == ["or( empty(#a), not( has_dups(#a) ) )"]
    assert parts.counters == []
    assert report.skipped == []


def test_odcs_property_duplicate_values_threshold() -> None:
    rule = {"metric": "duplicateValues", "mustBeLessThan": 3}
    parts, _ = _convert({"name": "a", "quality": [rule]})
    assert parts.line_checks == ["or( empty(#a), not( has_dups(#a) ) )"]
    assert parts.counters == [
        "and.nocontrib( not( empty(#a) ), has_dups(#a) ) -> counter.a_duplicate(1)"
    ]
    assert parts.last_checks == [
        "and.nocontrib( eq( count_lines(), total_lines() ), gte( @a_duplicate, 3 ) ) -> fail()"
    ]
    parts, _ = _convert({"name": "a", "required": True, "quality": [rule]})
    assert parts.line_args == ["string.notnone.distinct(#a)"]
    assert parts.counters == ["has_dups.nocontrib(#a) -> counter.a_duplicate(1)"]


def test_odcs_property_percent_threshold() -> None:
    parts, _ = _convert(
        {
            "name": "a",
            "quality": [
                {"metric": "nullValues", "mustBeLessThan": 5, "unit": "percent"}
            ],
        }
    )
    assert parts.line_args == ["string.notnone(#a)"]
    assert parts.last_checks == [
        "and.nocontrib( eq( count_lines(), total_lines() ), gte( multiply( divide( @a_null, "
        "subtract(total_lines(), 1) ), 100 ), 5 ) ) -> fail()"
    ]


def test_odcs_property_missing_values() -> None:
    rule = {
        "metric": "missingValues",
        "arguments": {"missingValues": [None, "", "N/A", "-"]},
        "mustBe": 0,
    }
    parts, report = _convert({"name": "a", "quality": [rule]})
    assert parts.line_args == ["string.notnone(#a)"]
    assert parts.line_checks == ['not( in(#a, "N/A|-") )']
    assert parts.counters == []
    assert report.skipped == []


def test_odcs_property_missing_values_without_empties() -> None:
    rule = {
        "metric": "missingValues",
        "arguments": {"missingValues": ["N/A"]},
        "mustBeLessThan": 2,
    }
    parts, _ = _convert({"name": "a", "quality": [rule]})
    assert parts.line_args == ["string(#a)"]
    assert parts.line_checks == ['or( empty(#a), not( in(#a, "N/A") ) )']
    assert parts.counters == ['in.nocontrib(#a, "N/A") -> counter.a_missing(1)']


def test_odcs_property_missing_values_default_is_null_or_empty() -> None:
    rule = {"metric": "missingValues", "mustBeLessThan": 2}
    parts, _ = _convert({"name": "a", "quality": [rule]})
    assert parts.line_args == ["string.notnone(#a)"]
    assert parts.line_checks == []
    assert parts.counters == ["empty.nocontrib(#a) -> counter.a_missing(1)"]


def test_odcs_property_missing_values_both_kinds_counted() -> None:
    rule = {
        "metric": "missingValues",
        "arguments": {"missingValues": [None, "N/A"]},
        "mustBeLessThan": 2,
    }
    parts, _ = _convert({"name": "a", "quality": [rule]})
    assert parts.counters == [
        'or.nocontrib( empty(#a), in(#a, "N/A") ) -> counter.a_missing(1)'
    ]


def test_odcs_property_missing_values_inexpressible() -> None:
    rule = {
        "metric": "missingValues",
        "arguments": {"missingValues": ["a|b"]},
        "mustBe": 0,
    }
    parts, report = _convert({"name": "a", "quality": [rule]})
    assert parts.line_checks == []
    assert _features(report) == [
        ("properties.a.quality[0].arguments.missingValues", "missingValues")
    ]


def test_odcs_property_v30_rule_name() -> None:
    parts, _ = _convert({"name": "a", "quality": [{"rule": "nullValues", "mustBe": 0}]})
    assert parts.line_args == ["string.notnone(#a)"]


@pytest.mark.parametrize(
    "rule,feature",
    [
        ({"metric": "rowCount", "mustBe": 0}, "quality.rowCount"),
        ({"metric": "nullValues"}, "quality.nullValues"),
        ({"type": "sql", "query": "SELECT 1", "mustBe": 1}, "quality.sql"),
        ({"type": "custom", "engine": "soda", "implementation": "x"}, "quality.custom"),
        ({"type": "text", "description": "d"}, "quality.text"),
    ],
)
def test_odcs_property_skipped_quality(rule: dict, feature: str) -> None:
    parts, report = _convert({"name": "a", "quality": [rule]})
    assert _features(report) == [("properties.a.quality[0]", feature)]
    assert parts.counters == [] and parts.last_checks == []


# ============================
# relationships
# ============================


def test_odcs_property_relationships() -> None:
    _, report = _convert({"name": "a", "relationships": [{"to": "b.c"}, {"to": "d.e"}]})
    assert _features(report) == [
        ("properties.a.relationships[0]", "relationship"),
        ("properties.a.relationships[1]", "relationship"),
    ]


def test_odcs_property_threshold_counters_do_not_collide() -> None:
    parts = CsvPathParts()
    report = ConversionReport()
    rule = {"metric": "nullValues", "mustBeLessThan": 3}
    for index, name in enumerate(["Order ID", "order_id"]):
        PropertyConverter(
            obj="t",
            prop={"name": name, "quality": [rule]},
            index=index,
            parts=parts,
            report=report,
        ).convert()
    assert parts.counters == [
        'empty.nocontrib(#"Order ID") -> counter.order_id_null(1)',
        "empty.nocontrib(#order_id) -> counter.order_id_null_2(1)",
    ]
    assert parts.last_checks[1] == (
        "and.nocontrib( eq( count_lines(), total_lines() ), gte( @order_id_null_2, 3 ) ) -> fail()"
    )


@pytest.mark.parametrize("threshold", [{"mustBe": 0}, {"mustBeLessThan": 2}])
def test_odcs_property_missing_values_empty_list(threshold: dict) -> None:
    rule = {"metric": "missingValues", "arguments": {"missingValues": []}, **threshold}
    parts, report = _convert({"name": "a", "quality": [rule]})
    assert parts.line_args == ["string(#a)"]
    assert parts.line_checks == [] and parts.counters == []
    assert _features(report) == [("properties.a.quality[0]", "quality.missingValues")]


def test_odcs_property_allowed_values_drop_empties() -> None:
    #
    # as in the official ODCS example quality/column-validity: empties in an
    # allowed-values list are governed by required/optional, not by the list
    #
    rule = {
        "metric": "invalidValues",
        "arguments": {"validValues": ["", None, "n/a"]},
        "mustBe": 0,
    }
    parts, report = _convert({"name": "a", "quality": [rule]})
    assert parts.line_checks == ['or( empty(#a), in(#a, "n/a") )']
    assert report.skipped == []
    parts, _ = _convert({"name": "a", "enum": [{"value": None}, {"value": "x"}]})
    assert parts.line_checks == ['or( empty(#a), in(#a, "x") )']


def test_odcs_property_allowed_values_only_empties() -> None:
    parts, report = _convert({"name": "a", "enum": ["", None]})
    assert parts.line_checks == []
    assert _features(report) == [("properties.a.enum", "enum")]
