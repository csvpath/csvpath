from dataclasses import dataclass
from typing import Any
from csvpath.matching.expression import Function
from csvpath.matching.functions import Count, Regex

class UnknownFunctionException(Exception):
    pass

class FunctionFactory:

    @classmethod
    def get_function(cls, matcher, name, p) -> Function:
        f = None
        if name == 'count':
            #count()                # number of matches (assuming the current also matches)
            #count(value)           # p[3] is equality or function to track number of times seen
            f = Count(matcher, p[1], p[3] if len(p) == 5 else None)

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
        elif name == 'regex':
            #(regex-string)         # match on a regular expression
            f = Regex(matcher, p[1], p[3])
            p[3].parent = f

        elif name == 'or':
            #(value, value...)      # match one
            pass
        elif name == 'every':
            #(number, value)        # match every n times a value is seen
            pass
        else:
            pass
            # generic function. ultimately we want an error here
            #raise UnknownFunctionException(f"no match for {name}")
        if f is None:
            print(f"WARNING: returning default function because no match for {name}")
            f = Function(matcher, p[1], p[3] if len(p) == 5 else None)
            if len(p) == 5:
                p[3].parent = f
        return f

