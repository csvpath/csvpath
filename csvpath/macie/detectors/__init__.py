"""detectors for managed data identifiers. Each takes its data from the
catalog's detectors section and finds occurrences in one cell. The
catalog's detector names map to classes here. A detector with
TAKES_PARAMETER = True gets one from its reference, e.g. "iban:GB". One
class can serve several detector names, each with its own catalog data,
e.g. GroupedDigitsDetector for ca_sin and uk_nhs."""

from .credit_card_detector import CreditCardDetector
from .grouped_digits_detector import GroupedDigitsDetector
from .iban_detector import IbanDetector
from .us_npi_detector import UsNpiDetector
from .us_ssn_detector import UsSsnDetector
from .vin_detector import VinDetector

DETECTORS = {
    "ca_sin": GroupedDigitsDetector,
    "credit_card": CreditCardDetector,
    "iban": IbanDetector,
    "us_npi": UsNpiDetector,
    "uk_nhs": GroupedDigitsDetector,
    "us_ssn": UsSsnDetector,
    "vin": VinDetector,
}
