
# Header

Always returns True to matches() and to_value(). Just a signal to other functions like any().

## Example

    $file.csv[*][ any(header(), "test") ]

This path matches when any column has the value `test`.



