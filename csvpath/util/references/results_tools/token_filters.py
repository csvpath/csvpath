import datetime
from datetime import time, timedelta, timezone
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.reference_exceptions import ReferenceException
from csvpath.util.references.results_tools.date_filter import DateFilter


class TokenFilters:
    #
    # these are just name_one_tokens. name_three_tokens are about csvpath identities; quite different
    #
    # we care about:
    #   - before (to)
    #   - after (from)
    #   - index
    #   - yesterday
    #   - today
    #   - first
    #   - last
    #   - all
    #   - date
    #   - two dates, between
    #

    @classmethod
    def update(cls, *, results: ReferenceResults, tokens: list[str]) -> None:
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
    def first_moment(cls, dt: datetime) -> datetime:
        return datetime.datetime.combine(dt.date(), time.min)

    @classmethod
    def filter(cls, results: ReferenceResults, tokens: list[str], token: str) -> None:
        tokens.remove(token)
        if results.files is None:
            raise ValueError("Result files cannot be None")
        if len(results.files) == 0:
            return
        if token is None:
            raise ValueError("Token cannot be None")
        #
        # let's filter
        #
        if token == "yesterday":
            end = datetime.datetime.now(timezone.utc)
            end = cls.first_moment(end)
            begin = end - timedelta(days=1)
            DateFilter.according_to_limit(results, begin, end, filter=True)
            return
        if token == "today":
            begin = datetime.datetime.now(timezone.utc)
            begin = cls.first_moment(begin)
            end = begin + timedelta(days=1)
            DateFilter.according_to_limit(results, begin, end, filter=True)
            return
        if token == "first":
            results.files = [results.files[0]]
            return
        if token == "last":
            results.files = [results.files[-1]]
            return
        if token == "all":
            return
        if DateFilter.is_date(token) and DateFilter.find_date(tokens) is not None:
            begin = DateFilter.to_date(token)
            begin = cls.first_moment(begin)
            end = DateFilter.to_date(token[0])
            end = cls.first_moment(end)
            end = end + timedelta(days=1)
            DateFilter.according_to_limit(results, begin, end, filter=True)
            return
        if DateFilter.is_date(token):
            begin = DateFilter.to_date(token)
            if "before" in tokens or "to" in tokens:
                DateFilter.everything_before(results, token)
                tokens.clear()
            elif "after" in tokens or "from" in tokens:
                DateFilter.everything_after(results, token)
                tokens.clear()
            else:
                begin = cls.first_moment(begin)
                end = begin + timedelta(days=1)
                DateFilter.according_to_limit(results, begin, end, filter=True)
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
        elif index is not None and len(tokens) > 0:
            raise ReferenceException("Cannot have an index that has a following token")

    @classmethod
    def _index(cls, tokens, token):
        try:
            return int(token)
        except (TypeError, ValueError):
            return None
