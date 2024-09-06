# pylint: disable=C0114
from .function import Function


class ValueProducer(Function):
    """base class for all value-oriented functions. a
    ValueProducer can determine a match, but only
    as an existence test or using the asbool qualifier.
    primarily ValueProducers are about returning
    specific values."""

    FOCUS = "ValueProducer"


class MatchDecider(Function):
    """base class for all match-oriented functions. a
    MatchDecider can produce a value based on its match
    result, but it is primarily a yes/no matcher, not
    a more specific value producer.

    keep in mind that some MatchDeciders generate
    significant data behind the scenes, some of which
    might be available in well-known variables.
    header_names_mismatch would be a good example of
    this dual-use capability."""

    FOCUS = "MatchDecider"


class SideEffect(Function):
    """base class for functions that are primarily available
    to create side-effects, rather than to produce values
    or vote on matching.

    examples of SideEffect functions include print(), stop()
    skip() and collect()."""

    FOCUS = "SideEffect"
