Increments a variable. The increment is 1 by default.

Counters must be named using a name qualifier. Without that, the ID
generated for your counter will be tough to use.

A name qualifier is an arbitrary name added with a dot after the
function name and before the parentheses. It looks like
counter.my_name()

┌──────────────────────────────────────────┐
│ Data signatures                          │
├──────────────────────────────────────────┤
│ counter( [amount to increment by: int] ) │
└──────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ Call signatures                                                                       │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ counter( [amount to increment by: Term|Function|Header|Variable|Reference|Equality] ) │
└───────────────────────────────────────────────────────────────────────────────────────┘
┌───────┬───────────────────────────────────────┐
│ Focus │ counter() produces a calculated value │
└───────┴───────────────────────────────────────┘
┌──────────────────┬─────────────────────┐
│ Match qualifiers │ onmatch             │
├──────────────────┼─────────────────────┤
│ Value qualifiers │ onmatch             │
├──────────────────┼─────────────────────┤
│ Name qualifier   │ optionally expected │
└──────────────────┴─────────────────────┘
... xpath
Xpath

Finds the value of an XPath expression given a match component
containing XML.

┌─────────────────────────────────────────────────────────────┐
│ Data signatures                                             │
├─────────────────────────────────────────────────────────────┤
│ xpath( from this XML: str|''|None, select this XPath: str ) │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Call signatures                                                                                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ xpath( from this XML: Term|Variable|Header|Function|Reference, select this XPath: Term|Variable|Header|Function|Reference ) │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌───────┬─────────────────────────────────────┐
│ Focus │ xpath() produces a calculated value │
└───────┴─────────────────────────────────────┘
┌──────────────────┬─────────┐
│ Match qualifiers │ onmatch │
├──────────────────┼─────────┤
│ Value qualifiers │ onmatch │
