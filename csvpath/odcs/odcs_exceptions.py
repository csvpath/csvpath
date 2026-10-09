class OdcsException(Exception):
    """raised when an ODCS contract cannot be converted to CsvPath at all:
    unreadable or schema-invalid input, an unsupported apiVersion, or a
    structural problem the converter cannot work around. Features that are
    merely untranslatable do not raise; they are skipped and listed in the
    ConversionReport."""
