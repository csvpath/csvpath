# pylint: disable=C0114
from .function import Function
from ..productions import Term, Header, Variable, ChildrenException


class Every(Function):
    """collects a regularly sampled subset of a value"""

    def check_valid(self) -> None:
        self.validate_two_args(right=[Term, Variable, Function, Header])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()

        if self.value is None:
            child = self.children[0]
            ###
            # 1. we store a count of values under the ID of left. this is the value.to_value
            # 2. we store the every-N-seen count under the qualifier or ID of every
            # 3. we match based on count % n == 0
            #
            self._id = (
                self.qualifier if self.qualifier is not None else self.get_id(self)
            )
            allcount = f"{self.get_id(self)}_{'every'}"
            tracked_value = child.left.to_value(skip=skip)
            cnt = self.matcher.get_variable(
                allcount, tracking=tracked_value, set_if_none=0
            )
            cnt += 1
            self.matcher.set_variable(allcount, tracking=tracked_value, value=cnt)
            every = child.right.to_value()
            # if we aren't an int we're going to blow up.
            # what's the best option? a default int? for now just raising.
            try:
                every = int(every)
            except Exception:
                raise ChildrenException("every()'s second argument must be an int")
            if cnt % every == 0:
                self.value = True
            else:
                self.value = False
            everycount = self.matcher.get_variable(
                self._id, tracking=self.value, set_if_none=0
            )
            everycount += 1
            self.matcher.set_variable(self._id, tracking=self.value, value=everycount)
        return self.value
