import json
import logging

from csvpath.util.file_readers import DataFileReader


class JsonFileUtility:
    #
    # loads a JSON file the framework writes itself (the root ledgers, for
    # now) and, when it does not parse, raises an error that names the file
    # and says what probably happened. json.JSONDecodeError gives neither:
    # no path, and a position without a reason (RC triage A19 part 3,
    # David 2026-11-16). The causes are best guesses from where parsing
    # stopped, so the message says "probably".
    #
    RECOVERY = (
        "Keep a copy of the file, then restore it from a backup, or remove "
        "the damaged part: a ledger is a JSON list with one {...} entry per "
        "event."
    )

    @classmethod
    def load(cls, *, path: str):
        """the parsed JSON at `path`; a ValueError naming the file and the
        likely cause when it does not parse."""
        if not isinstance(path, str):
            raise TypeError(f"path must be a str, not {type(path)}")
        if path.strip() == "":
            raise ValueError("path cannot be empty")
        logger = logging.getLogger(cls.__name__)
        try:
            with DataFileReader(path) as reader:
                text = reader.source.read()
            if isinstance(text, bytes):
                text = text.decode("utf-8")
        except UnicodeDecodeError as e:
            msg = (
                f"{path} is not UTF-8 text (byte {e.start}): it was probably "
                f"damaged or overwritten by another file. {cls.RECOVERY}"
            )
            logger.error(msg)
            raise ValueError(msg) from e
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            msg = f"{path} {cls.diagnosis(text=text, error=e)}. {cls.RECOVERY}"
            logger.error(msg)
            raise ValueError(msg) from e

    @classmethod
    def diagnosis(cls, *, text: str, error: json.JSONDecodeError) -> str:
        """what probably happened, from where and why parsing stopped."""
        if text is None or error is None:
            raise ValueError("text and error cannot be None")
        blank = text.strip("\x00 \t\r\n") == ""
        if not blank and "\x00" in text:
            # zero bytes are what some filesystems leave after a crash
            return (
                "contains zero bytes: a write was probably interrupted "
                "(a crash or a full disk)"
            )
        if blank:
            return (
                "is empty: a write was probably interrupted (a crash, a "
                "killed process or a full disk)"
            )
        if error.msg.startswith("Extra data"):
            return (
                f"holds more than one JSON value (line {error.lineno}, column "
                f"{error.colno}): two writes probably landed on top of each "
                "other, e.g. two processes writing it at once"
            )
        # a cut-off string reports where the string opened, not the end of
        # the file, so its message is the sign (reviewer on #726)
        if error.pos >= len(text.rstrip()) or error.msg.startswith(
            "Unterminated string"
        ):
            return (
                "ends partway through an entry: a write was probably "
                "interrupted or the disk filled up"
            )
        return (
            f"is not valid JSON at line {error.lineno}, column {error.colno} "
            f"({error.msg}): it may have been edited by hand"
        )
