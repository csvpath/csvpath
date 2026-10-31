import logging
import re

from .macie_exceptions import MacieException


class ArnUtility:
    """Macie ARNs in csvpath metadata. The metadata parser treats every ":"
    as the start of a new key, so an ARN is written with "|" in place of
    each ":" and swapped back when read. "|" can't occur in a Macie ARN, so
    the swap is unambiguous.

    In the csvpath body, inside a quoted string, an ARN needs no swap."""

    SEPARATOR = ":"
    SUBSTITUTE = "|"
    #
    # arn:partition:macie2:region:account:resource. partition is e.g. aws,
    # aws-cn, aws-us-gov. region is empty for no Macie resource we know of,
    # but the format allows it.
    #
    MACIE_ARN = re.compile(r"arn:[a-z0-9-]+:macie2:[a-z0-9-]*:\d{12}:[A-Za-z0-9/_-]+")

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def check(cls, *, arn: str) -> str:
        """returns the ARN if it is a well-formed Macie ARN; raises otherwise"""
        if not isinstance(arn, str):
            raise TypeError(f"arn must be a str, not {type(arn)}")
        if cls.MACIE_ARN.fullmatch(arn) is None:
            cls._fail(f"Not a Macie ARN: {arn!r}")
        return arn

    @classmethod
    def to_metadata(cls, *, arn: str) -> str:
        """an ARN as a csvpath metadata value"""
        return cls.check(arn=arn).replace(cls.SEPARATOR, cls.SUBSTITUTE)

    @classmethod
    def from_metadata(cls, *, value: str) -> str:
        """a metadata value written by to_metadata(), back to the ARN"""
        if not isinstance(value, str):
            raise TypeError(f"value must be a str, not {type(value)}")
        if cls.SEPARATOR in value:
            cls._fail(
                f"Metadata ARN {value!r} contains {cls.SEPARATOR!r}; "
                f"write it with {cls.SUBSTITUTE!r}"
            )
        return cls.check(arn=value.replace(cls.SUBSTITUTE, cls.SEPARATOR))

    @classmethod
    def _fail(cls, msg: str) -> None:
        cls.logger().error(msg)
        raise MacieException(msg)
