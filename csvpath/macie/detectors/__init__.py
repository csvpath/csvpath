"""detectors for managed data identifiers. Each takes its data from the
catalog's detectors section and finds occurrences in one cell. The
catalog's detector names map to classes here. A detector with
TAKES_PARAMETER = True gets one from its reference, e.g. "iban:GB"."""

from .credit_card_detector import CreditCardDetector
from .iban_detector import IbanDetector
from .us_npi_detector import UsNpiDetector
from .us_ssn_detector import UsSsnDetector

DETECTORS = {
    "credit_card": CreditCardDetector,
    "iban": IbanDetector,
    "us_npi": UsNpiDetector,
    "us_ssn": UsSsnDetector,
}
