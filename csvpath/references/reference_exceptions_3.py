class ReferenceException3(Exception):
    """raised for semantic problems with a parsed references-v3
    reference that the grammar deliberately doesn't enforce -- e.g. a
    missing name_three where the reference's datatype requires one. see
    reference_grammar_3.py's module docstring for why that check is
    deferred out of the grammar."""
