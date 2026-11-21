import logging

from ...reference_exceptions_3 import ReferenceException3, ReferenceRuntimeException3


class BareNameUtility:
    """the check that a name a reference reads from a run instance's
    directory -- ':file("orders.parquet")', ':printouts("greetings")' -- is a
    bare file name, not a path. A path could leave the instance directory:
    '../../config.ini', '/etc/passwd', 'C:secret.txt'.

    Used by File3 and Printouts3 on a literal when the function is built
    and on a resolved @variable or "{...}" value when it resolves
    (check_resolved()), and by ResultsReferenceFinder3 again just before it
    joins the name onto the instance directory, so no route reaches the
    file system with a path. Until 2026-11-21 only File3's literal was
    checked: ':file(@f)' with '../../x.txt' passed, and ':printouts()' was
    never checked (reviewer on #790)."""

    # a separator, a parent step, a Windows drive, or a NUL. '..' is refused
    # anywhere in a name, so the legitimate 'a..b.txt' is refused too: the
    # safe side, since a separator-free '..' cannot climb anyway but a
    # backend that treats another character as a separator could
    FORBIDDEN = ("/", "\\", "..", ":", "\x00")

    @classmethod
    def problem(cls, name) -> "str | None":
        """why `name` is not a bare file name, or None if it is"""
        if not isinstance(name, str):
            return f"it must be a string, not {type(name).__name__}"
        if name.strip() == "":
            return "it cannot be empty"
        if name.strip(".") == "":
            # '.' is the instance directory itself (reviewer on #791)
            return "it cannot be only dots"
        found = [f for f in cls.FORBIDDEN if f in name]
        if found:
            shown = ", ".join(repr(f) for f in found)
            return f"it must be a bare file name, not a path (found {shown})"
        return None

    @classmethod
    def check(cls, *, function_name: str, name) -> None:
        """raises a ReferenceException3 unless `name` is a bare file name"""
        if not function_name:
            raise ValueError("function_name cannot be None or empty")
        problem = cls.problem(name)
        if problem is not None:
            raise ReferenceException3(
                f":{function_name}({name!r}) reads a file in the run instance's "
                f"directory, so {problem}."
            )

    @classmethod
    def check_at_join(cls, *, function_name: str, name) -> None:
        """the last check, where a name is joined onto the instance
        directory. The earlier checks should make it unreachable, so a
        failure here means a route around them: it is logged, and raised as
        a ReferenceRuntimeException3"""
        try:
            cls.check(function_name=function_name, name=name)
        except ReferenceException3 as e:
            logging.getLogger(__name__).error(
                "a path reached the instance directory join: %s", e
            )
            raise ReferenceRuntimeException3(str(e)) from None
