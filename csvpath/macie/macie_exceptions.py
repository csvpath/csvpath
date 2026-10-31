class MacieException(Exception):
    """raised when a Macie wrapper cannot be used at all: unreadable or
    schema-invalid input, an unsupported format version, or references
    inside the wrapper that do not line up (e.g. a selected custom data
    identifier with no definition). Problems recorded at download time,
    such as an unreadable allow list, do not raise; they are kept in the
    wrapper's warnings."""
