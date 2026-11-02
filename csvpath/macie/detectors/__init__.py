"""detectors for managed data identifiers. Each takes its data from the
catalog's detectors section and finds occurrences in one cell. The
catalog's detector names map to classes here."""

from .credit_card_detector import CreditCardDetector

DETECTORS = {
    "credit_card": CreditCardDetector,
}
