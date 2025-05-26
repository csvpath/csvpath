# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args
from csvpath.matching.productions import Matchable


class Count(ValueProducer):
    """counts matches by default. when fed other match components
    it can count more specific things."""

    def check_valid(self) -> None:  # pylint: disable=W0246
        # note to self: no specific validity checks from way back
        # these args may need work
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Returns the number of matches.

                When used alone count() gives the total matches seen up to the current line in the file.

                Matches can be scoped down to a contained existence test or equality.
                Counting an equality means a function, term, variable, or header compared
                to another function, term, variable, or header.

                When count() is scoped to its contained value, the count is of the values seen.
                If it is a bool, the count is the number of Trues and the number of Falses.
                If an int, it is a count of each value seen.

                For example, take count( empty( #zipcode ) )

                This use of count() counts the number of times it sees True and False. Whereas, count( #zipcode )
                Counts the number of times each value of zipcode is seen.

                When counting the values it sees, count() stores the value-integer pairs in
                a variable under a key identifying the count function. The ID of the count
                function is a hash by default, making it difficult for a human to understand
                which count the key represents. To name the count use a qualifier count().

                A name qualifier is a name that follows the function name separated by a
                dot. For example: count.red_cars(#0="red").

                count() can take the onmatch qualifier. When there is a contained value and
                onmatch, count only increments if its contained value matches. For example:
                $[*][count.onmatch( in(#firstname,"Bug|Bird|Ants") ) == 2]

                This path counts first names that match the in() function. If the count equals
                2 the row will also match. This is a different behavior from that of other match
                components in that count is using onmatch to look inward, rather than at its
                siblings. Bear in mind, count() without a contained value only increments
                when the row matches. In that case, onmatch would add nothing.
            """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset(0)
        a = self.args.argset()
        a.arg(name="eval", types=[None, Matchable], actuals=[None, Any])
        self.args.validate(self.siblings())
        #
        super().check_valid()  # pylint: disable=W0246
        # re: W0246: Matchable handles this class's children

    #
    # not easy to move this to _produce_value() because it does onmatch
    # deeper in the logic. can be done, but a PIA. later.
    #
    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
            # return self.value if self.value is not None else True
        if self.value is None:
            if self._function_or_equality:
                self.value = self._get_contained_value(skip=skip)
            else:
                self.value = (
                    self._get_match_count() + 1
                )  # we're eager to +1 because we don't
                # contribute to if there's a match
        return self.value  # or not. we have to act as if.

    #
    # we always match. regardless of if any contained condition matches.
    #
    def matches(self, *, skip=None) -> bool:
        # we get a value because that's how we are sure to count
        self.to_value(skip=skip)
        return self.default_match()  # pragma: no cover

    def _get_match_count(self) -> int:
        if not self.matcher or not self.matcher.csvpath:
            # this could be testing; otherwise invalid.
            return -1
        return self.matcher.csvpath.current_match_count

    def _get_contained_value(self, *, skip=None) -> Any:
        if skip is None:
            skip = []
        self._id = self.first_non_term_qualifier(
            self.get_id(self._function_or_equality)
        )
        #
        # to_value() is often going to be a bool based on matches().
        # but in a case like: count(now('yyyy-mm-dd')) it would not be
        #
        tracked_value = self._function_or_equality.to_value(skip=skip)
        cnt = self.matcher.get_variable(self._id, tracking=tracked_value, set_if_none=0)
        if not self.onmatch or self._function_or_equality.matches(skip=skip):
            cnt += 1
            self.matcher.set_variable(self._id, tracking=tracked_value, value=cnt)
        return 0 if cnt is None else cnt
