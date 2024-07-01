from csvpath.matching.functions.function import Function
from csvpath.matching.functions.count import Count
from csvpath.matching.functions.regex import Regex
from csvpath.matching.functions.length import Length
from csvpath.matching.functions.notf import Not
from csvpath.matching.functions.now import Now
from csvpath.matching.functions.inf import In
from csvpath.matching.functions.concat import Concat
from csvpath.matching.functions.lower import Lower
from csvpath.matching.functions.upper import Upper
from csvpath.matching.functions.percent import Percent
from csvpath.matching.functions.below import Below
from csvpath.matching.functions.above import Above
from csvpath.matching.functions.first import First
from csvpath.matching.productions.expression import Matchable

class UnknownFunctionException(Exception):
    pass

class InvalidChildException(Exception):
    pass

class FunctionFactory:

    @classmethod
    def get_function(cls, matcher, *, name:str, child:Matchable=None ) -> Function:
        if child and not isinstance(child, Matchable):
            raise InvalidChildException(f"{child} is not a valid child")
        f = None
        if name == 'count':
            #count()                # number of matches (assuming the current also matches)
            #count(value)           # p[3] is equality or function to track number of times seen
            f = Count(matcher, name, child)
        elif name == 'length':
            #(value)                # returns the length of the value
            f = Length(matcher, name, child)
        elif name == 'regex':
            f = Regex(matcher, name, child)
        elif name == 'not':
            f = Not(matcher, name, child)
        elif name == 'now':         # a date
            f = Now(matcher, name, child)
        elif name == 'in':
            f = In(matcher, name, child)
        elif name == 'concat':
            f = Concat(matcher, name, child)
        elif name == 'lower':
            f = Lower(matcher, name, child)
        elif name == 'upper':
            f = Upper(matcher, name, child)
        elif name == 'percent':
            f = Percent(matcher, name, child)
        elif name == 'below':
            f = Below(matcher, name, child)
        elif name == 'above':
            f = Above(matcher, name, child)
        elif name == 'first':
            f = First(matcher, name, child)
        else:
            raise UnknownFunctionException(f"{name}")

        if child:
            child.parent = f
        return f

