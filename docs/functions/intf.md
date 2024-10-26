
# Int, Float, Num

These functions:
- Identity numbers as types for structural validation
- Convert values to numbers

In CsvPath numbers are often upcast to floats before operations. In some cases it may be desirable to convert floats back to ints or declare the number of places.

## int()

Converts its argument to an int, if possible. Beyond the regular way Python converts to int, it will attempt to:
- Swap a `None` for `0`
- Strip a string to empty and treat as `0`

If the conversion is possible there is a match.


## float()

Converts its argument to a float similar to the way `int()` does, if possible. If the conversion is possible there is a match.

## num()

Used for its value, `num()` converts any type to `float`, if possible, with the exception leaving `int`s and `bool`s as they are.

In matching num takes up to five arguments:
- The required value from any match component
- Optionally:
    - Max number of digits before the decimal
    - Min number of digits before the decimal
    - Max number of digits after the decimal
    - Min number of digits after the decimal

In the max/min values a `-1` means we don't care. Effectively a `-1` min is `0`.

It is certainly straightforward to handle this validation in a regular expression; however, using `num()` has more type-intentionality and requires less understanding of regular expressions.

# Examples

```bash
    $file.csv[*][ line( string(#firstname), num(#age, 3, 1, 0) )]
```

This declares that the age header value is a whole number < 999. More validation of ages may be needed.

```bash
    $file.csv[*][line( int(#year), num(#rain_in_year, 0, 0, 2 ) )]
```
This csvpath presents the number of inches of rain each year in Luxor, Egypt. .99 is large enough.

