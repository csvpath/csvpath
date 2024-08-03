
# First

Matches the first time a value is seen. A variable tracks the first line numbers for each value. First tracks None and other values that could be hard to interpret. Internally, the magic number First.NEVER = -9999999999 indicates an unset value.

First can take the `onmatch` qualifier.

## Examples

    $file.csv[*][first.folks(#firstname)]

This path matches when the value of the `firstname` has not been seen before. It results in a variable like:

    {'folks': {'David': 1}}

Multiple values can be used as arguments to first().

    $file.csv[*][first.dude(#firstname, #lastname)]

This path matches the first instance of the firstname and lastname column values together. The comparison simply concatenates the values. The result is a variable like:

    {'dude': {'DavidKermit': 5}}



