
# Variable

Always returns True to matches() and to_value(). Just a signal to other functions like any().

## Example

    $file.csv[*][ any(variable(), "test") ]

This path matches when any variable has the value `test`.



