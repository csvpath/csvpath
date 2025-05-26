from typing import Any, List
from csvpath.util.config import OnError
from csvpath.modes.error_mode import ErrorMode


class ErrorCommunications:
    """this class determines how errors should be handled. basically there
    are two types of errors:
    1. built-in validation errors that come from the Args class in two
       passes: pre-run match component tree checking and line by line
       expected values validation
    2. rules errors where match components raise due to circumstances
       having to do with the rules they were set up to implement. e.g.
       an end() that is given a -1 will pass it's Args validation
       because Args only looks at the type of a value, not the value
       itself, but end() takes a positive int so it raises an exception
    the error policy in config/config.ini (or whereever your config is)
    is the baseline. however, every csvpath can override the config
    for some of the error handling using a comment with the metadata
    field validation-mode. config
    has two setting values not tracked in metadata: quiet and log.
    """

    def __init__(self, csvpath=None, csvpaths=None) -> None:
        self._csvpath = csvpath
        self._csvpaths = csvpaths
        if not csvpath and not csvpaths:
            raise ValueError("Must have either a CsvPath or CsvPaths instance")

    def do_i_quiet(self) -> bool:
        return self.in_policy(OnError.QUIET.value)

    def do_i_raise(self) -> bool:
        if self._csvpath and self._csvpath.raise_validation_errors is not None:
            return self._csvpath.raise_validation_errors
        return self.in_policy(OnError.RAISE.value)

    def do_i_collect(self) -> bool:
        if self._csvpath and self._csvpath.collect_validation_errors is not None:
            return self._csvpath.collect_validation_errors
        return self.in_policy(OnError.COLLECT.value)

    def do_i_print(self) -> bool:
        if self._csvpath and self._csvpath.print_validation_errors is not None:
            return self._csvpath.print_validation_errors
        return self.in_policy(OnError.PRINT.value)

    def do_i_print_expanded(self) -> bool:
        ret = False
        c = self._csvpath if self._csvpath is not None else self._csvpaths
        if c is not None:
            ret = (
                c.config.get(
                    section="errors", name=ErrorMode.CONFIG_KEY, default=ErrorMode.BARE
                )
                == ErrorMode.FULL
            )
        if self._csvpath and self._csvpath.error_mode == ErrorMode.FULL:
            ret = True
        return ret

    def do_i_stop(self) -> bool:
        mode = None
        if self._csvpath and self._csvpath.stop_on_validation_errors is not None:
            #
            # looks wrong. function in FlightPath is not correct. doesn't match other do_i_...
            #
            mode = self._csvpath.stop_on_validation_errors
            #
            # this was a change made for flightpath. not sure it works. it may well work.
            # however atm visibility isn't great. come back later.
            #
            # return self._csvpath.stop_on_validation_errors
        policy = self.in_policy(OnError.STOP.value)
        return mode is True or policy is True

    def do_i_fail(self) -> bool:
        if self._csvpath and self._csvpath.fail_on_validation_errors is not None:
            return self._csvpath.fail_on_validation_errors
        return self.in_policy(OnError.FAIL.value)

    def in_policy(self, v) -> bool:
        if self._csvpath:
            return v in self._csvpath.config.csvpath_errors_policy
        return v in self._csvpaths.config.csvpaths_errors_policy
