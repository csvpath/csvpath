import logging
from dataclasses import dataclass, field

from .conversion_report import ConversionReport
from .odcs_contract_loader import OdcsContractLoader
from .odcs_exceptions import OdcsException
from .schema_object_converter import SchemaObjectConverter


@dataclass
class OdcsConversion:
    """the result of converting one ODCS contract.

    csvpaths: schema object name -> csvpath text, in contract order. Each
              csvpath has no filename in its root, ready to be loaded into a
              named-paths group.
    report:   the validation-relevant features that were not translated
    """

    csvpaths: dict[str, str] = field(default_factory=dict)
    report: ConversionReport = field(default_factory=ConversionReport)


class OdcsConverter:
    """converts an ODCS data contract into CsvPath Validation Language, one
    csvpath per schema object.

        contract = OdcsContractLoader.from_path(path="orders.odcs.yaml")
        conversion = OdcsConverter(contract=contract).convert()
        conversion.csvpaths["orders"]   # csvpath text
        conversion.report.skipped       # what was not translated

    The contract is validated against the official ODCS JSON Schema for its
    apiVersion before conversion.
    """

    def __init__(self, *, contract: dict) -> None:
        if contract is None:
            raise ValueError("contract cannot be None")
        self.contract = OdcsContractLoader.validate(contract=contract)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def convert(self) -> OdcsConversion:
        objects = self.contract.get("schema") or []
        if len(objects) == 0:
            msg = f"ODCS contract {self.contract.get('id')} has no schema objects"
            self.logger.error(msg)
            raise OdcsException(msg)
        conversion = OdcsConversion()
        seen = set()
        for obj in objects:
            name = obj.get("name")
            if name in seen:
                msg = f"Duplicate schema object name {name}"
                self.logger.error(msg)
                raise OdcsException(msg)
            seen.add(name)
            csvpath = SchemaObjectConverter(
                contract=self.contract, obj=obj, report=conversion.report
            ).convert()
            if csvpath is not None:
                conversion.csvpaths[name] = csvpath
        if len(conversion.csvpaths) == 0:
            msg = (
                f"ODCS contract {self.contract.get('id')} has no schema objects "
                "with properties to convert"
            )
            self.logger.error(msg)
            raise OdcsException(msg)
        return conversion
