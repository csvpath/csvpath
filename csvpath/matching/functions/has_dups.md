
# Has_dups

The `has_dups()` matches any row that matches a previous row.

`has_dups()` can take one or more headers to find the duplicate rows based only on those values. When it has no arguments it compares the entire row for duplicates.

The function collects the line numbers of each duplicate, as well as that of the original row that was duplicated.

`has_dups()` can take the `onmatch` qualifier.


## Example

    $test[*][
        @dups = has_dups(#1)
        not(empty(@dups)) -> print("line $.line_count has dups in $.variables.dups")
    ]

This path prints every time a duplicate is found. The print string includes the list of line numbers that duplicate the current row.


