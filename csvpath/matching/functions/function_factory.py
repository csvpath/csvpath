from csvpath.matching.functions.function import Function
from csvpath.matching.functions.count import Count
from csvpath.matching.functions.regex import Regex
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

        elif name == 'regex':
            f = Regex(matcher, name, child)

        elif name == 'scanned':     # count lines we checked for match
            pass
        elif name == 'lines':       # count lines to this point in the file
            pass
        elif name == 'after':
            #(value)                # finds things after a date, number, string
            pass
        elif name == 'before':
            #(value)                # finds things before a date, number, string
            pass
        elif name == 'now':         # a date
            pass
        elif name == 'between':
            #(from, to)             # between dates, numbers, strings
            pass
        elif name == 'type':        # returns the type of a field
            pass
        elif name == 'not':
            #(value)                # negates a value
            pass
        elif name == 'length':
            #(value)                # returns the length of the value
            pass
        elif name == 'random':
            #(type, from, to)       # returns a random number, string date within a range
            #(list)                 # pick from a list
            pass
        elif name == 'in':
            #(list-source)          # match in a list from a file
            pass
        elif name == 'or':
            #(value, value...)      # match one
            pass
        elif name == 'every':
            #(number, value)        # match every n times a value is seen
            pass
        else:
            raise UnknownFunctionException(f"{name}")

        if child:
            child.parent = f
        return f

