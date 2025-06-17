import datetime
from datetime import timedelta, timezone
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.tools.date_completer import DateCompleter
from csvpath.util.references.files_tools.range_finder import RangeFinder


class DateFinder:
    @classmethod
    def update(
        cls, results: ReferenceResults, name: str, tokens: list[str], filter=False
    ) -> None:
        #
        # filter == True is to thin out results.files
        # filter == False is to pull in from manifest.json
        #
        # ref = results.ref
        try:
            token = "after"
            #
            # if we're a date our default is :after, but we'll use before if we find
            # there is not also a date token. if there is not, the before is for us.
            # but if there is a date token the other token before or after is for that
            # date. practically, if we had 2025-01-:2021-01:before we would have junk.
            # in a perfect world we'd take that to mean: 2025-01-:before:2021-01-:after
            # but it would be simpler for the query writer to just write a sensible
            # order.
            #
            if cls._has_date_token(tokens):
                # we stay with token == "after" the default
                ...
            else:
                if "before" in tokens or "to" in tokens:
                    token = "before"

            #
            # this can blow up. it's the reason for the try.
            #
            s = DateCompleter.get(name)
            dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
            #
            # this is an interesting point because what we do depends on pointers
            # and may have been different intentions at different times. today --
            # and i think this is logical
            #  - after takes a timestamp forward to the present
            #  - before takes the history from moment 1 to the timestamp
            #  - all is all
            #  - last-before (or last?) is the most recent to the timestamp
            #  - first is the first following the timestamp
            # and for the future
            #  - if we do 'on' it would be within the most specific unit (e.g. '2025-05-10' would be on that day
            #  - if we did a between it would be timestamp:timestamp
            #
            # long story short, we can keep _find_in_date for the other place used, but we need
            # a method that looks at a range of dates, not just a day
            #
            #
            # after is the default. if we have an exact match on date it is still effectively on-or-after
            # at least for now.
            #
            #
            # pondering: before and after seem exclusive whereas from and to seem inclusive.
            #
            _ = RangeFinder.for_token(results, adate=dat, token=token, filter=filter)
            results.files = _
            #
            # we modify the names one or three with the completed date. that is idempotent.
            # we also remove the token. if we found a date we'll consume the token.
            #
            if results.ref.name_one == name:
                results.ref.name_one = s
                results.ref.name_one_tokens.remove(token)
            elif results.ref.name_three == name:
                results.ref.name_three = s
                results.ref.name_three_tokens.remove(token)
        except (ValueError, TypeError):
            #
            # we return none because this is expected. we won't like the date
            # string in some cases because it's not a date string. in those cases
            # we want the if/else series of checks above to continue with other
            # strategies for finding results.
            #
            # import traceback
            # print(traceback.format_exc())
            return
        finally:
            ...

    @classmethod
    def _has_date_token(cls, tokens: list[str]) -> bool:
        for _ in tokens:
            try:
                s = DateCompleter.get(_)
                datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
                return True
            except Exception:
                ...
        return False
