
# Add, Subtract, Multiply, Divide, Mod, Int

These arithmetic functions work mostly the way you would expect.

Numbers are upcast to floats before the operations.

## subtract() and minus()

Subtracts any number of numbers or makes a number negative.

`minus` is an alias for `subtract` that makes more intuitive sense when you are just making a negative number.

## add()

Adds any number of numbers together.

## multiply()

Multiplies any number of numbers together.

## divide()

Divides any number of numbers. `divide()` will return `nan` when divide by `0` is attempted.

## mod()

Returns the modulus of two numbers. `mod()` upcasts to `float` and rounds to the hundredths.

## int()

Converts its argument to an int, if possible. If the convert to int fails it will attempt to:
- Swap a `None` for `0`
- Identify the empty string and treat as `0`
- Swap `False` for `0`

If those attempts don't work it raises `ChildrenException`.


## Examples

```bash
    $file.csv[*][column(minus(2))]
```

Finds the name of the 2nd column from the right.

```bash
    $file.csv[*][@b = subtract(@a, 2)]
```

Sets the value of `b` to be the value of `a` minus 2.

```bash
    $[*][
        @workdays = multiply(count_lines(), 5, #weeks_per_year) ]
```

Finds the number of work days by multiplying three numbers.


