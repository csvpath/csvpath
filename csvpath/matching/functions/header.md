
# Header

`header()` has two functions:

- It may be used as a signal to other functions like any()
- Given an int or name, it matches if there is a column for that header index or name

## Examples

    $file.csv[*][ any(header(), "test") ]

This first path matches when any column has the value `test`.

    $file.csv[1][ header("firstname") ]

Matches if `#firstname` exists as a valid header, regardless of if there is a value in `#firstname` in any given row. To test if there is a value of `#firstname` for a particular row you would write `exists(#firstname)` or just `#firstname`.

