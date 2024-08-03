
# Qualifiers


Variables and some functions can take qualifiers on their name. A qualifier takes the form of a dot plus a qualification name. At the moment there are only four qualifiers:

- `onmatch` to indicate that action on the variable or function only happens when the whole path matches a row
- `onchange` set on a variable to indicate that a row should only match when the variable is set to a new value
- `asbool` set on a variable or header to have its value interpreted as a bool rather than just a simple `is not None` test
- `nocontrib` set on the left hand side of a `->` to indicate that there should be no impact on the row match. E.g. `$test[*][yes() last.nocontrib() -> print("last line!")]` will collect all rows but only print on the last; whereas, without `nocontrib` only the last line would be collected.
- An arbitrary string to add a name for the function's internal use, typically to name a variable

Qualifiers look like:

    [ @myvar.onmatch = yes() ]

Or:

    [ @i = increment.this_is_my_increment.onmatch(yes(), 3) ]

When multiple qualifiers are used order is not important.

Qualifiers are actively being discovered and implementation is opportunistic. Eventually the feature will need to be formalized. Watch this space!





