
# When

Activates its right hand side when the left hand matches. When does not affect the match of a row. It always returns True to matches() and to_value().

## Example

    $file.csv[*][
                    @counting=count_lines()
                    when(@counting==5, @full=True)
                ]

This path sets the `full` variable to `True` when it hits line 5.



