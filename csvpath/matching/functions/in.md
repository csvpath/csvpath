
# In

Returns True to matches() when a calculated value matches to values in a delimited string. The calculated value is a term, variable, header, or function. The delimited string is values separated by pipes.

## Examples

    $file.csv[*][in(#firstname, "Tom|Dick|Harry")]

This path matches when the value of the `firstname` column is `Tom`, `Dick`, or `Harry`.

    $file.csv[*][
                    @x.onmatch = count()
                    in(#firstname,"Bug|Bird|Ants")
    ]

This path sets `x` to the number of times the `firstname` column is `Bug`, `Bird`, or `Ants`.

    $file.csv[*][
                    @x.onmatch = count(in(#firstname,"Bug|Bird|Ants"))
                    in(#firstname,"Bug|Bird|Ants")
    ]

This path sets `x` to the number of times the `firstname` column is `Bug`, `Bird`, or `Ants`. It also sets the count variable `True` to the same number. Of the two paths, this is obviously not the better choice, but it is an interesting example.

