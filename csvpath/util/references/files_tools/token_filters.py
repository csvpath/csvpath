import datetime
from csvpath.util.references.reference_results import ReferenceResults
from ..reference_exceptions import ReferenceException
from csvpath.util.references.tools.date_completer import DateCompleter
from csvpath.util.references.files_tools.range_finder import RangeFinder
from csvpath.util.references.files_tools.day_finder import DayFinder


class TokenFilters:
    @classmethod
    def update(cls, results: ReferenceResults, tokens: list[str]) -> None:
        #
        # tokens are the tokens of one of the four ref names. they must be
        # copied into a mutable list so we can track what tokens we've handled
        #
        ts = tokens[:]
        for t in tokens:
            cls.filter(results, ts, t)
            if len(ts) == 0:
                return

    @classmethod
    def filter(cls, results: ReferenceResults, tokens: list[str], token: str) -> None:
        tokens.remove(token)
        if results.files is None:
            raise ValueError("Result files cannot be None")
        if len(results.files) == 0:
            return
        if token is None:
            raise ValueError("Token cannot be None")
        if token in ["yesterday", "today"]:
            DayFinder.update(results, tokens, token)
            #
            # day finder consumes the 2nd token. e.g. today:1 or today:last are both
            # handled at the same time. we get two tokens. that means after dayfinder
            # we're done.
            #
            tokens.clear()
            return
        if token == "first":
            results.files = [results.files[0]]
            return
        if token == "last":
            results.files = [results.files[-1]]
            return
        if token == "all":
            return
        #
        # see if we have an index. if we have just one index we'll
        # attempt to use it and return.
        #
        index = cls._index(tokens, token)
        if index is not None and len(tokens) == 0:
            try:
                results.files = [results.files[index]]
            except Exception:
                results.files = []
            return
        #
        # if we don't have an index in i we might have one
        # in the 2nd token.
        #
        elif not index and len(tokens) > 0:
            try:
                index = int(tokens[0])
            except Exception:
                ...
        #
        # now we either have:
        #   - index + before/after/from/to  -OR-
        #   - date + before/after/from/to
        #
        date = cls._complete_date(token)
        if date is None:
            date = cls._date_string(tokens, token)
        else:
            if len(tokens) > 0:
                token = tokens[0]
                tokens.remove(token)
            else:
                token = "after"
        #
        if date and index:
            #
            # both date and index are points in time that need direction. (tho in principle
            # both can also be a singular pointer; regardless can't have both)
            #
            raise ReferenceException("Cannot have both a date token and an index token")
        #
        if date:
            date = datetime.datetime.strptime(date, "%Y-%m-%d_%H-%M-%S")
            if token == "before" or token == "to":
                RangeFinder.all_before(results, date)
            elif token == "after" or token == "from":
                RangeFinder.all_after(results, date)
        elif index:
            if len(results.files) <= index:
                results.files = []
            elif token == "before":
                if index - 1 >= 0:
                    results.files = results.files[0 : index - 1]
                else:
                    results.files = []
            elif token == "to":
                results.files = results.files[0:index]
            elif token == "after":
                if len(results.files) > index + 1:
                    results.files = results.files[index + 1 :]
                else:
                    results.files = []
            elif token == "from":
                results.files = results.files[index:]
        else:
            raise ReferenceException(
                f"Cannot have token {token} in this context with date: {date} and index: {index}"
            )

    @classmethod
    def _index(cls, tokens, token):
        t = tokens[0] if len(tokens) > 0 else token
        i = None
        try:
            i = int(t)
        except (TypeError, ValueError):
            ...
        if i and not token == str(i):
            try:
                int(token)
                raise ReferenceException("Cannot have two indexes")
            except (TypeError, ValueError):
                ...
                # this is good, just one index
        return i

    @classmethod
    def _date_string(cls, tokens, token):
        t1 = token
        t2 = tokens[0] if len(tokens) > 0 else None
        d = None
        try:
            d = DateCompleter.get(t1)
        except ValueError:
            ...
        if not d and t2:
            try:
                d = DateCompleter.get(t1)
            except ValueError:
                ...
                # we have no date. that's fine, atm.
        return d

    @classmethod
    def _complete_date(cls, token):
        try:
            return DateCompleter.get(token)
        except ValueError:
            return None
