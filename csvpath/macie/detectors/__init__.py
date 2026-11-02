"""detectors for managed data identifiers. Each takes its data from the
catalog's detectors section and finds occurrences in one cell. The
catalog's detector names map to classes here."""

from .credit_card_detector import CreditCardDetector
from .us_npi_detector import UsNpiDetector
from .us_ssn_detector import UsSsnDetector

DETECTORS = {
    "credit_card": CreditCardDetector,
    "us_npi": UsNpiDetector,
    "us_ssn": UsSsnDetector,
}
