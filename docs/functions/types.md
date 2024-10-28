
# Types

The core types functions give you a way to identify the correct type of a header value. Whereas the `int()` function will convert a value to an int, the purpose of the type function `integer()` is to indicate that a value should be an int and to check if it is in fact an int.

This difference is important when you are setting up structural or schema-based validation. CsvPath uses the `line()` function to declare the types of tabular data. Line uses the type functions as its primitives.

## String
`string()` takes three arguments:
- The name of a header
- An optional max length or `none()` to indicate no constraint
- An optional min length or `none()` to indicate no constraint; however, using `none()` would be superfluous since the argument is optional

## Decimal
`decimal()` represents numbers with decimal points. In Python terms, the float type. `decimal()` takes three arguments:
- The name of a header
- An optional max value or `none()` to indicate no constraint
- An optional min value or `none()` to indicate no constraint; however, using `none()` would be superfluous since the argument is optional

To limit matching to values with a `.` character add the qualifier `strict`.

## Integer
`integer()` is the same as `decimal()`, except whole numbers only, no decimal points.

## Boolean
`boolean()` represents true/false values. The values recognized are:
- True is:
    - `True` or `yes()`
    - `"true"`
    - `1`
- False is:
    - `False` or `no()`
    - `None` or `none()`
    - `"false"`
    - `0`

## Date

## None
`none()` is the absence of a value. In Python, `None`. In CSVs, two delimiters with no non-whitespace characters between them is also a none value. However, the absence of a value is not treated as a boolean `False`, even though an explicit `None` is considered `False`.

## Blank
`blank()` represents a header whose type is unknown, changes, or is immaterial.

# Examples



