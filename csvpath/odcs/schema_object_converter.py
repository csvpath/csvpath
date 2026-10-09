import logging

from .conversion_report import ConversionReport
from .csvpath_parts import CsvPathParts
from .odcs_exceptions import OdcsException
from .property_converter import PropertyConverter
from .quality_utility import QualityUtility as quut
from .threshold_utility import ThresholdUtility as thut


class SchemaObjectConverter:
    """converts one ODCS schema object (one table) into one csvpath"""

    VALIDATION_MODE = "print, no-raise, no-fail, no-stop"
    ROWS = "subtract(total_lines(), 1)"

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
            if metric != "rowCount":
                self._skip(
                    location=location,
                    feature=f"quality.{metric}",
                    reason=f"Schema-level {metric} is not yet supported.",
                )
                continue
            try:
                fail_when = thut.fail_when(value=self.ROWS, rule=q)
            except ValueError as e:
                self._skip(location=location, feature="quality.rowCount", reason=f"{e}")
                continue
            #
            # before the header skip, so a header-only file is checked too
            #
            self.parts.first_checks.append(
                f"and.nocontrib( last(), {fail_when} ) -> fail()"
            )

    def _relationships(self) -> None:
        for j, _ in enumerate(self.obj.get("relationships") or []):
            self._skip(
                location=f"relationships[{j}]",
                feature="relationship",
                reason="Relationships span tables; a csvpath validates one file.",
            )
