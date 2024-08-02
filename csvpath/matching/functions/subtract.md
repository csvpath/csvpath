
# Subtract

Subtracts two numbers or makes a number negative.

`minus` is an alias for `subtract` that makes more intuitive sense when you are just making a negative number.

## Examples

    $file.csv[*][column(minus(2))]

Finds the name of the 2nd column from the right.

    $file.csv[*][@b = subtract(@a, 2)]

Sets the value of `b` to be the value of `a` minus 2.

