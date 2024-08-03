
# Qualifiers

Variables and some functions can take qualifiers on their name. A qualifier takes the form of a dot plus a qualification name. Qualifiers look like:

    [ @myvar.onmatch = yes() ]

Or:

    [ @i = increment.this_is_my_increment.onmatch(yes(), 3) ]

When multiple qualifiers are used order is not important.

Qualifiers are new and being added opportunistically. See the individual function docs for which qualifiers are available on a function.


## Well-known Qualifiers
At the moment there are only four qualifiers.

### onmatch
`onmatch` indicates that action on the variable or function only happens when the whole path matches a row

### onchange
`onchange` set on a variable to indicate that a row should only match when the variable is set to a new value

### asbool
`asbool` set on a variable or header to have its value interpreted as a bool rather than just a simple `is not None` test

### nocontrib
`nocontrib` set on the left hand side of a `->` to indicate that there should be no impact on the row match. E.g. `$test[*][yes() last.nocontrib() -> print("last line!")]` will collect all rows but only print on the last; whereas, without `nocontrib` only the last line would be collected.


## Arbitrary Names
You can also add an arbitrary string to a function name. This additional name is for the function's internal use, typically to name a variable.

As an example, the `tally()` function sets an internal variable under the key 'tally'. This variable would be overwritten if you used two `tally()` functions in one csvpath. Adding a name qualifier fixes that problem:

    $test[*][ tally.my_tally(#firstname) tally.my_other_tally(#lastname)]








