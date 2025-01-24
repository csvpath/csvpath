
# Types

These types work with `line()` to enable structural validation. Structural, or schema, validation is what XSD, DDL, and JSON Schema do. They define entities (or call them tables, structures, etc.) that describe the expected form of the data. CsvPath offers the same capability in a format that is similar to DDL's.

The core type functions give you a way to identify the correct type of a header value. CsvPath uses the `line()` function to declare the order of typed-headers. The type functions and their qualifiers are the `line()` function's complete set of primitives. There can be multiple `line()` functions per line of data, even overlapping ones.

See the links below for more discussion and examples of CsvPath's structural validation capabilities.

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

## Date and Datetime

## Email and URL

## None
`none()` is the absence of a value. In Python, `None`. In CSVs, two delimiters with no non-whitespace characters between them is also a none value. However, the absence of a value is not treated as a boolean `False`, even though an explicit `None` is considered `False`.

## Blank
`blank()` represents a header whose type is unknown, changes, or is immaterial.

## Wildcard
`wildcard()` stands in for any number of headers in a row. It takes an integer indicating the number of headers expected or a `*` to indicate an unknown number of headers. Headers that are wildcarded are not type checked.

# Examples

```python
    $[*][
      line.distinct.person(
        string.notnone("firstname", 25),
        blank("middlename"),
        string.notnone("lastname", 35, 2),
        wildcard(4)
    )
    line.address(
        wildcard(3),
        string.notnone("street"),
        string.notnone("city"),
        string.notnone("state"),
        integer.notnone("zip")
    )
    count_headers_in_line() == 7
]
```
This csvpath defines a line as having two entities side-by-side. The first is a person. Because of the `distinct` qualifier, we know that the combination of their first name and family name must be unique within the dataset.

A person is made up of three header values: `firstname`, `middlename`, and `lastname`. `firstname` must be greater than or equal to one character long and `25` or fewer characters. `lastname` must be `2` or more characters and `35` or fewer. Both `firstname` and `lastname are required to be filled. `middlename` can be empty.

Sitting right beside each person is an address. We know address is beside person because:
- CsvPath validates line-by-line
- The person entity has the first three positions, then a wildcard of four headers.
- The address wildcards three headers, then takes the following four positions.

There cannot be further headers in a row. We can tell only the two entities are allowed because `count_headers_in_line()` requires 7 headers. That is a line-by-line check. If we want to also check the header line we could use `header_count()`.

See <a target='_blank' href='https://www.csvpath.org/getting-started/your-first-validation-the-easy-way'>this How-to</a> and this <a target='_blank' href='https://www.csvpath.org/topics/validation/schemas-or-rules'>description of CsvPath structural validation</a> for more examples and discussion of type-based validation.

