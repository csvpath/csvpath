import logging

from .conversion_report import ConversionReport
from .csvpath_parts import CsvPathParts
from .csvpath_text_utility import CsvPathTextUtility as csut
from .odcs_exceptions import OdcsException
from .property_converter import PropertyConverter
from .quality_utility import QualityUtility as quut
from .threshold_utility import ThresholdUtility as thut


class SchemaObjectConverter:
    """converts one ODCS schema object (one table) into one csvpath"""

    VALIDATION_MODE = "print, no-raise, no-fail, no-stop"

    def __init__(self, *, contract: dict, obj: dict, report: ConversionReport) -> None:
        if not isinstance(contract, dict):
            raise TypeError(f"contract must be a dict, not {type(contract)}")
        if not isinstance(obj, dict):
            raise TypeError(f"obj must be a dict, not {type(obj)}")
        if not isinstance(report, ConversionReport):
            raise TypeError(f"report must be a ConversionReport, not {type(report)}")
        if not isinstance(obj.get("name"), str) or obj["name"].strip() == "":
            raise ValueError(f"A schema object must have a name: {obj}")
        self.contract = contract
        self.obj = obj
        self.name = obj["name"]
        self.report = report
        self.parts = CsvPathParts()
        #
        # schema-level duplicateValues rules, resolved in _quality() so the
        # report stays in document order, but emitted after the properties
        # so their checks follow the per-column checks
        #
        self._duplicates: list[tuple[list[tuple[str, bool]], dict, list[str]]] = []

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def convert(self) -> str:
        properties = self.obj.get("properties") or []
        if len(properties) == 0:
            msg = f"Schema object {self.name} has no properties to convert"
            self.logger.error(msg)
            raise OdcsException(msg)
        self.parts.metadata = {
            "id": self.name,
            "odcs-contract-id": f"{self.contract['id']}",
            "odcs-contract-version": f"{self.contract['version']}",
            "odcs-schema-object": self.name,
            "validation-mode": self.VALIDATION_MODE,
        }
        self._quality()
        for index, prop in enumerate(properties):
            PropertyConverter(
                obj=self.name,
                prop=prop,
                index=index,
                parts=self.parts,
                report=self.report,
            ).convert()
        self._emit_duplicates()
        self._relationships()
        return self.parts.render()

    def _skip(self, *, location: str, feature: str, reason: str) -> None:
        self.report.skip(
            obj=self.name, location=location, feature=feature, reason=reason
        )

    def _quality(self) -> None:
        for j, q in enumerate(self.obj.get("quality") or []):
            location = f"quality[{j}]"
            kind = q.get("type", "library")
            if kind != "library":
                self._skip(
                    location=location,
                    feature=f"quality.{kind}",
                    reason=quut.skip_reason(kind=kind, rule=q),
                )
                continue
            metric = quut.metric(rule=q)
            if metric == "rowCount":
                self._row_count(rule=q, location=location)
            elif metric == "duplicateValues":
                self._duplicate_values(rule=q, location=location)
            else:
                self._skip(
                    location=location,
                    feature=f"quality.{metric}",
                    reason=f"Schema-level {metric} is not yet supported.",
                )

    def _row_count(self, *, rule: dict, location: str) -> None:
        if thut.is_percent(rule=rule):
            self._skip(
                location=location,
                feature="quality.rowCount",
                reason="A percent rowCount has no meaning.",
            )
            return
        try:
            fail_when = thut.fail_when(value=thut.ROWS, rule=rule)
        except ValueError as e:
            self._skip(location=location, feature="quality.rowCount", reason=f"{e}")
            return
        #
        # before the header skip, so a header-only file is checked too
        #
        self.parts.first_checks.append(
            f"and.nocontrib( last(), {fail_when} ) -> fail()"
        )

    def _duplicate_values(self, *, rule: dict, location: str) -> None:
        names = (rule.get("arguments") or {}).get("properties")
        if not isinstance(names, list) or len(names) == 0:
            self._skip(
                location=location,
                feature="quality.duplicateValues",
                reason="Schema-level duplicateValues needs arguments.properties.",
            )
            return
        try:
            thut.operator(rule=rule)
        except ValueError as e:
            self._skip(
                location=location, feature="quality.duplicateValues", reason=f"{e}"
            )
            return
        by_name = {
            p.get("name"): (index, p)
            for index, p in enumerate(self.obj.get("properties") or [])
        }
        columns = []
        for name in names:
            if name not in by_name:
                self._skip(
                    location=location,
                    feature="quality.duplicateValues",
                    reason=f"duplicateValues names unknown property {name}.",
                )
                return
            index, prop = by_name[name]
            column = prop.get("physicalName") or name
            h = csut.header(name=column, index=index)
            columns.append((h, prop.get("required") is True))
        self._duplicates.append((columns, rule, names))

    def _emit_duplicates(self) -> None:
        for columns, rule, names in self._duplicates:
            headers = ", ".join(h for h, _ in columns)
            #
            # a row with an empty value in any of the columns is never a
            # duplicate (SQL semantics)
            #
            optional = [h for h, required in columns if not required]
            check = f"not( has_dups({headers}) )"
            if optional:
                empties = ", ".join(f"empty({h})" for h in optional)
                check = f"or( {empties}, {check} )"
            self.parts.line_checks.append(check)
            if thut.is_zero_tolerance(rule=rule):
                continue
            when = f"has_dups.nocontrib({headers})"
            if optional:
                not_empty = ", ".join(f"not( empty({h}) )" for h in optional)
                when = f"and.nocontrib( {not_empty}, has_dups({headers}) )"
            base = csut.variable(name="_".join(names), suffix="duplicate")
            self.parts.add_threshold(base=base, when=when, rule=rule)

    def _relationships(self) -> None:
        for j, _ in enumerate(self.obj.get("relationships") or []):
            self._skip(
                location=f"relationships[{j}]",
                feature="relationship",
                reason="Relationships span tables; a csvpath validates one file.",
            )
