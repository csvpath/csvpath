from csvpath.matching.functions.boolean.yes import Yes


class SampleInternal(Yes):
    """a stand-in for an add-on function, e.g. one of Macie's. its module
    must only be imported when a csvpath uses it."""


class NotAFunction:
    pass
