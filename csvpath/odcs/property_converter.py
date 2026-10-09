from .conversion_report import ConversionReport
from .csvpath_parts import CsvPathParts
from .csvpath_text_utility import CsvPathTextUtility as csut
from .jdk_date_format_utility import JdkDateFormatUtility as jdut
from .quality_utility import QualityUtility as quut
from .threshold_utility import ThresholdUtility as thut


class PropertyConverter:
    """converts one ODCS schema property (one column) into a line()
    argument plus any checks, counters, and last-line checks it needs.
    Untranslatable features are added to the report, not raised.

    The rules are recorded, with worked examples, in
    tests/odcs/test_resources/normative/README.md.
    """

    STRING_FORMATS = {"email": "email", "uuid": "uuid", "uri": "url"}
    UNTYPED = ["array", "object", "map", "vector"]
    DATE_TYPES = ["date", "timestamp", "time"]
    BOOLEAN_VALUES = '"true|false|1|0"'

    #
    # logicalTypeOptions handled per logicalType. any other key present is
    # reported as skipped.
    #
    HANDLED_OPTIONS = {
        "string": {"minLength", "maxLength", "pattern", "format"},
        "integer": {
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
        },
        "date": {
            "format",
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
        },
    }
    HANDLED_OPTIONS["number"] = HANDLED_OPTIONS["integer"]
    HANDLED_OPTIONS["timestamp"] = HANDLED_OPTIONS["date"] | {
        "timezone",
        "defaultTimezone",
    }
    HANDLED_OPTIONS["time"] = HANDLED_OPTIONS["timestamp"]

    def __init__(
        self,
        *,
        obj: str,
        prop: dict,
        index: int,
        parts: CsvPathParts,
        report: ConversionReport,
    ) -> None:
        if not isinstance(obj, str) or obj.strip() == "":
            raise ValueError("obj must be a non-empty str")
        if not isinstance(prop, dict):
            raise TypeError(f"prop must be a dict, not {type(prop)}")
        if not isinstance(prop.get("name"), str) or prop["name"].strip() == "":
            raise ValueError(f"A property must have a name: {prop}")
        if not isinstance(parts, CsvPathParts):
            raise TypeError(f"parts must be CsvPathParts, not {type(parts)}")
        if not isinstance(report, ConversionReport):
            raise TypeError(f"report must be a ConversionReport, not {type(report)}")
        self.obj = obj
        self.prop = prop
        self.parts = parts
        self.report = report
        self.name = prop["name"]
        column = prop.get("physicalName") or self.name
        self.h = csut.header(name=column, index=index)
        self.location = f"properties.{self.name}"
        self.logical_type = prop.get("logicalType") or "string"
        self.options = prop.get("logicalTypeOptions") or {}
        self.required = prop.get("required") is True
        self.unique = prop.get("unique") is True

    def convert(self) -> None:
        self._quality_flags()
        lt = self.logical_type
        if lt == "string":
            self._string()
        elif lt in ["integer", "number"]:
            self._number()
        elif lt == "boolean":
            self._boolean()
        elif lt in self.DATE_TYPES:
            self._date()
        else:
            self._untyped()
        if lt not in self.UNTYPED:
            self._unique_check()
        self._unhandled_options()
        self._enum()
        self._quality()
        self._relationships()

    # ============================
    # helpers
    # ============================

    def _skip(self, *, location: str, feature: str, reason: str) -> None:
        self.report.skip(
            obj=self.obj, location=location, feature=feature, reason=reason
        )

    def _qualifiers(self) -> str:
        #
        # .distinct treats two empty values as duplicates. empty values are
        # never duplicates (SQL semantics), so .distinct is only used where
        # empties are already rejected; see _unique_check().
        #
        if self.required:
            return ".notnone" + (".distinct" if self.unique else "")
        return ""

    def _unique_check(self) -> None:
        if self.unique and not self.required:
            self.parts.line_checks.append(
                f"or( empty({self.h}), not( has_dups({self.h}) ) )"
            )

    def _per_line(self, *, condition: str) -> str:
        # an optional column may be empty; required is enforced in the line()
        if self.required:
            return condition
        return f"or( empty({self.h}), {condition} )"

    def _max_min_args(self, *, max_key: str, min_key: str) -> str:
        mx = self.options.get(max_key)
        mn = self.options.get(min_key)
        if mx is None and mn is None:
            return ""
        mxs = "none()" if mx is None else csut.number(value=mx)
        if mn is None:
            return f", {mxs}"
        return f", {mxs}, {csut.number(value=mn)}"

    # ============================
    # types
    # ============================

    def _string(self) -> None:
        fmt = self.options.get("format")
        fn = "string"
        if fmt in self.STRING_FORMATS:
            fn = self.STRING_FORMATS[fmt]
            for key in ["maxLength", "minLength"]:
                if key in self.options:
                    self._skip(
                        location=f"{self.location}.logicalTypeOptions.{key}",
                        feature=key,
                        reason=f"{fn}() takes no length; {key} is not checked.",
                    )
            self.parts.line_args.append(f"{fn}{self._qualifiers()}({self.h})")
        else:
            if fmt is not None:
                self._skip(
                    location=f"{self.location}.logicalTypeOptions.format",
                    feature=f"format.{fmt}",
                    reason=f"No CsvPath equivalent for string format {fmt}.",
                )
            args = self._max_min_args(max_key="maxLength", min_key="minLength")
            self.parts.line_args.append(f"string{self._qualifiers()}({self.h}{args})")
        pattern = self.options.get("pattern")
        if pattern is not None:
            try:
                literal = csut.regex(pattern=pattern)
            except ValueError as e:
                self._skip(
                    location=f"{self.location}.logicalTypeOptions.pattern",
                    feature="pattern",
                    reason=f"{e}",
                )
                return
            self.parts.line_checks.append(
                self._per_line(condition=f"regex({literal}, {self.h})")
            )

    def _number(self) -> None:
        fn = "integer" if self.logical_type == "integer" else "decimal"
        args = self._max_min_args(max_key="maximum", min_key="minimum")
        self.parts.line_args.append(f"{fn}{self._qualifiers()}({self.h}{args})")
        emin = self.options.get("exclusiveMinimum")
        if emin is not None:
            n = csut.number(value=emin)
            self.parts.line_checks.append(
                self._per_line(condition=f"gt({self.h}, {n})")
            )
        emax = self.options.get("exclusiveMaximum")
        if emax is not None:
            n = csut.number(value=emax)
            self.parts.line_checks.append(
                self._per_line(condition=f"gt({n}, {self.h})")
            )
        multiple = self.options.get("multipleOf")
        if multiple is not None:
            self._multiple_of(multiple=multiple)

    def _multiple_of(self, *, multiple) -> None:
        #
        # mod() rounds its result to 2 places, so a float remainder near the
        # divisor (e.g. 114.99999 % 5) reads as 5.0, not 0. integer divisors
        # are exact.
        #
        if isinstance(multiple, float) and not multiple.is_integer():
            self._skip(
                location=f"{self.location}.logicalTypeOptions.multipleOf",
                feature="multipleOf",
                reason=(
                    "mod() rounds to 2 places, so a non-integer multipleOf "
                    "cannot be checked reliably."
                ),
            )
            return
        n = csut.number(value=multiple)
        self.parts.line_checks.append(
            self._per_line(condition=f"eq( mod({self.h}, {n}), 0 )")
        )

    def _boolean(self) -> None:
        if self.required:
            self.parts.line_args.append(f"boolean{self._qualifiers()}({self.h})")
            return
        #
        # optional booleans work around issues #300 and #302: blank() in the
        # line() and an explicit check of exactly what boolean() accepts
        #
        self.parts.line_args.append(f"blank({self.h})")
        self.parts.line_checks.append(
            f"or( empty({self.h}), in( lower( strip({self.h}) ), {self.BOOLEAN_VALUES} ) )"
        )

    def _date_format(self) -> str | None:
        fmt = self.options.get("format")
        if fmt is not None:
            try:
                return jdut.to_strftime(pattern=fmt)
            except ValueError as e:
                self._skip(
                    location=f"{self.location}.logicalTypeOptions.format",
                    feature="format",
                    reason=f"{e}. Values are parsed leniently instead.",
                )
                return None
        if self.logical_type == "date":
            return jdut.ISO_DATE
        if self.logical_type == "time":
            return jdut.ISO_TIME
        # a timestamp with no format is parsed leniently
        return None

    def _date(self) -> None:
        fn = "date" if self.logical_type == "date" else "datetime"
        fmt = self._date_format()
        farg = "" if fmt is None else f", {csut.string(value=fmt)}"
        if self.required:
            self.parts.line_args.append(f"{fn}{self._qualifiers()}({self.h}{farg})")
        else:
            #
            # optional dates work around issue #300: blank() in the line()
            # and the date check outside it
            #
            self.parts.line_args.append(f"blank({self.h})")
            self.parts.line_checks.append(
                f"or( empty({self.h}), {fn}({self.h}{farg}) )"
            )
        self._date_bounds(fn=fn, fmt=fmt, farg=farg)

    def _date_bounds(self, *, fn: str, fmt: str | None, farg: str) -> None:
        field_value = f"{fn}({self.h}{farg})"
        formats = [f for f in [fmt, self._iso_format()] if f is not None]
        formats = list(dict.fromkeys(formats))
        for key in ["minimum", "exclusiveMinimum", "maximum", "exclusiveMaximum"]:
            bound = self.options.get(key)
            if bound is None:
                continue
            bound_format = jdut.parsing_format(value=f"{bound}", formats=formats)
            if bound_format is None:
                self._skip(
                    location=f"{self.location}.logicalTypeOptions.{key}",
                    feature=key,
                    reason=f"Cannot parse {key} {bound} with {formats}.",
                )
                continue
            b = f"{fn}({csut.string(value=f'{bound}')}, {csut.string(value=bound_format)})"
            if key == "minimum":
                condition = f"gte( {field_value}, {b} )"
            elif key == "exclusiveMinimum":
                condition = f"gt( {field_value}, {b} )"
            elif key == "maximum":
                condition = f"lte( {field_value}, {b} )"
            else:
                condition = f"gt( {b}, {field_value} )"
            self.parts.line_checks.append(self._per_line(condition=condition))

    def _iso_format(self) -> str:
        if self.logical_type == "date":
            return jdut.ISO_DATE
        if self.logical_type == "time":
            return jdut.ISO_TIME
        return "%Y-%m-%dT%H:%M:%S"

    def _untyped(self) -> None:
        self.parts.line_args.append(f"blank({self.h})")
        reason = (
            f"{self.logical_type.capitalize()} values have no CsvPath type; "
            "the column is checked for presence only."
        )
        if self.required or self.unique:
            reason += " required and unique are not checked."
        self._skip(
            location=self.location,
            feature=f"logicalType.{self.logical_type}",
            reason=reason,
        )

    def _unhandled_options(self) -> None:
        if self.logical_type in self.UNTYPED:
            return
        handled = self.HANDLED_OPTIONS.get(self.logical_type, set())
        for key in self.options:
            if key not in handled:
                self._skip(
                    location=f"{self.location}.logicalTypeOptions.{key}",
                    feature=key,
                    reason=f"{key} is not yet supported.",
                )

    # ============================
    # allowed values
    # ============================

    def _in_condition(self, *, values: list, location: str, feature: str) -> str | None:
        #
        # empty values are governed by required/optional, not by the list,
        # so a null or "" in an allowed-values list is dropped
        #
        values = [v for v in values if v is not None and v != ""]
        if len(values) == 0:
            self._skip(
                location=location,
                feature=feature,
                reason="The list has only empty values; empties follow required.",
            )
            return None
        try:
            return f"in({self.h}, {csut.in_values(values=values)})"
        except ValueError as e:
            self._skip(location=location, feature=feature, reason=f"{e}")
            return None

    def _enum(self) -> None:
        enum = self.prop.get("enum")
        if enum is None:
            return
        values = [e["value"] if isinstance(e, dict) else e for e in enum]
        condition = self._in_condition(
            values=values, location=f"{self.location}.enum", feature="enum"
        )
        if condition is not None:
            self.parts.line_checks.append(self._per_line(condition=condition))

    # ============================
    # quality
    # ============================

    def _quality_flags(self) -> None:
        #
        # under decision 2, lines that break a nullValues, missingValues, or
        # duplicateValues rule never match, whatever the threshold; a
        # threshold only adds a count. so these rules set required/unique
        # before the line() argument is built.
        #
        for q in self.prop.get("quality") or []:
            if q.get("type", "library") != "library":
                continue
            metric = quut.metric(rule=q)
            if metric == "nullValues":
                self.required = True
            elif metric == "missingValues":
                empties, _ = self._missing_values(rule=q)
                self.required = self.required or empties
            elif metric == "duplicateValues":
                self.unique = True

    def _missing_values(self, *, rule: dict) -> tuple[bool, list]:
        """(whether null or empty string counts as missing, the other
        values that count as missing). With no arguments, missing means
        null or empty."""
        args = rule.get("arguments") or {}
        values = args.get("missingValues", [None, ""])
        empties = any(v is None or v == "" for v in values)
        others = [v for v in values if v is not None and v != ""]
        return empties, others

    def _quality(self) -> None:
        for j, q in enumerate(self.prop.get("quality") or []):
            location = f"{self.location}.quality[{j}]"
            kind = q.get("type", "library")
            if kind != "library":
                self._skip(
                    location=location,
                    feature=f"quality.{kind}",
                    reason=quut.skip_reason(kind=kind, rule=q),
                )
                continue
            self._library(rule=q, location=location)

    def _library(self, *, rule: dict, location: str) -> None:
        metric = quut.metric(rule=rule)
        try:
            zero = thut.is_zero_tolerance(rule=rule)
        except ValueError as e:
            self._skip(location=location, feature=f"quality.{metric}", reason=f"{e}")
            return
        if metric == "invalidValues":
            self._invalid_values(rule=rule, location=location, zero=zero)
        elif metric == "nullValues":
            # .notnone is set by _quality_flags()
            if not zero:
                self._threshold(
                    suffix="null", rule=rule, when=f"empty.nocontrib({self.h})"
                )
        elif metric == "missingValues":
            self._missing(rule=rule, location=location, zero=zero)
        elif metric == "duplicateValues":
            # uniqueness is set by _quality_flags()
            if not zero:
                when = f"has_dups.nocontrib({self.h})"
                if not self.required:
                    when = (
                        f"and.nocontrib( not( empty({self.h}) ), has_dups({self.h}) )"
                    )
                self._threshold(suffix="duplicate", rule=rule, when=when)
        else:
            self._skip(
                location=location,
                feature=f"quality.{metric}",
                reason=f"Library metric {metric} is not yet supported on a property.",
            )

    def _missing(self, *, rule: dict, location: str, zero: bool) -> None:
        empties, others = self._missing_values(rule=rule)
        if not empties and not others:
            self._skip(
                location=location,
                feature="quality.missingValues",
                reason="missingValues lists no values.",
            )
            return
        values = None
        if others:
            try:
                values = csut.in_values(values=others)
            except ValueError as e:
                self._skip(
                    location=f"{location}.arguments.missingValues",
                    feature="missingValues",
                    reason=f"{e}",
                )
                return
            # empty values are handled by .notnone, set in _quality_flags()
            self.parts.line_checks.append(
                self._per_line(condition=f"not( in({self.h}, {values}) )")
            )
        if zero:
            return
        if empties and values:
            when = f"or.nocontrib( empty({self.h}), in({self.h}, {values}) )"
        elif empties:
            when = f"empty.nocontrib({self.h})"
        else:
            when = f"in.nocontrib({self.h}, {values})"
        self._threshold(suffix="missing", rule=rule, when=when)

    def _invalid_values(self, *, rule: dict, location: str, zero: bool) -> None:
        args = rule.get("arguments") or {}
        conditions = []
        if "validValues" in args:
            c = self._in_condition(
                values=args["validValues"],
                location=f"{location}.arguments.validValues",
                feature="validValues",
            )
            if c is not None:
                conditions.append(c)
        if "pattern" in args:
            try:
                conditions.append(
                    f"regex({csut.regex(pattern=args['pattern'])}, {self.h})"
                )
            except ValueError as e:
                self._skip(
                    location=f"{location}.arguments.pattern",
                    feature="pattern",
                    reason=f"{e}",
                )
        if len(conditions) == 0:
            if "validValues" not in args and "pattern" not in args:
                self._skip(
                    location=location,
                    feature="quality.invalidValues",
                    reason="invalidValues needs validValues or pattern arguments.",
                )
            return
        condition = (
            conditions[0] if len(conditions) == 1 else f"and( {', '.join(conditions)} )"
        )
        self.parts.line_checks.append(self._per_line(condition=condition))
        if not zero:
            #
            # empty values are nullValues/missingValues, not invalidValues
            #
            when = f"not.nocontrib( or( empty({self.h}), {condition} ) )"
            self._threshold(suffix="invalid", rule=rule, when=when)

    def _threshold(self, *, suffix: str, rule: dict, when: str) -> None:
        base = csut.variable(name=self.name, suffix=suffix)
        self.parts.add_threshold(base=base, when=when, rule=rule)

    # ============================
    # relationships
    # ============================

    def _relationships(self) -> None:
        for j, _ in enumerate(self.prop.get("relationships") or []):
            self._skip(
                location=f"{self.location}.relationships[{j}]",
                feature="relationship",
                reason="Relationships span tables; a csvpath validates one file.",
            )
