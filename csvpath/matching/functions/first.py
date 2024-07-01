from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
import datetime

class First(Function):

    def __init__(self, matcher, name:str=None, child:Any=None):
        super().__init__(matcher, child=child, name=name)
        self._my_value_or_none = -9999 # when this var is None we match

    def to_value(self) -> Any:
        if len(self.children) != 1:
            self.matcher.print(f"Firt.to_value: must have 1 child: {self.children}")
            raise ChildrenException("First function must have 1 child")
        if self._my_value_or_none == -9999:
            child = self.children[0]
            value = f"{child.to_value()}"
            my_id = self.get_id()
            v = self.matcher.get_variable(my_id, tracking=value )
            if v is None:
                self.matcher.set_variable(my_id, tracking=value, value=self.matcher.csvpath.current_line_number())
            #
            # when we have no earlier value we are first, so we match
            #
            self._my_value_or_none = v
        return self._my_value_or_none

    def matches(self) -> bool:
        #
        # when there is no earlier value we match
        #
        if self._my_value_or_none == -9999:
            self.to_value()
        v = self._my_value_or_none
        return v is None




