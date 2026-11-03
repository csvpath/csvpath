"""detectors for managed data identifiers. Each takes its data from the
catalog's detectors section and finds occurrences in one cell. The
catalog's detector names map to classes here. A detector with
TAKES_PARAMETER = True gets one from its reference, e.g. "iban:GB". One
class can serve several detector names, each with its own catalog data,
e.g. GroupedDigitsDetector for ca_sin and uk_nhs, and EsIdDetector for
es_dni and es_nie."""

from .bank_account_detector import BankAccountDetector
from .cl_rut_detector import ClRutDetector
from .credit_card_detector import CreditCardDetector
from .es_id_detector import EsIdDetector
from .grouped_digits_detector import GroupedDigitsDetector
from .iban_detector import IbanDetector
from .us_npi_detector import UsNpiDetector
from .us_ssn_detector import UsSsnDetector
from .vin_detector import VinDetector

DETECTORS = {
    "ar_sube": GroupedDigitsDetector,
    "bank": BankAccountDetector,
    "br_cnpj": GroupedDigitsDetector,
    "br_cpf": GroupedDigitsDetector,
    "ca_sin": GroupedDigitsDetector,
    "cl_rut": ClRutDetector,
    "credit_card": CreditCardDetector,
    "es_dni": EsIdDetector,
    "es_nie": EsIdDetector,
    "iban": IbanDetector,
    "in_aadhaar": GroupedDigitsDetector,
    "us_npi": UsNpiDetector,
    "uk_nhs": GroupedDigitsDetector,
    "us_ssn": UsSsnDetector,
    "vin": VinDetector,
}
