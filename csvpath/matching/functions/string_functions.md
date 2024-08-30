
# String Functions

The string handling functions behave much like their Python equivalents.

### concat(value, value, ...)

Concatenates any number of strings.

### length(value)

Same as you would expect.

### min_length(value, int) and max_length(value, int)

`min_length()` and `max_length()` return True if the stringified value is more than or less than the integer provided. The functionality can also be achieved using `above()` and `below()` or `between()`, but the min and max functions are obviously simpler.

### lower(value)

Same as you would expect.

### starts_with(does_this, start_with_this)

Checks if the first value, stringified, starts with the second value. The values are stripped.

### strip(value)

Same as you would expect.

### substring(value, int)

Substring starting from left and including the number of characters indicated. The value is stringified, so you can substring essentially anything.

### upper(value)

Same as you would expect.

## Examples

```bash
    $file.csv[*][
        @name = concat( #firstname, " ", #lastname )
        @name = strip(@name)
        @len = length(#firstname)
        @first = substring(@name, @len)
        @lower = lower(@name)
        @badge = upper(value)
    ]
```

This csvpath uses the string functions in their obvious ways.

```bash
    $file.csv[*][
        @name = #firstname
        @name_length = length(@name)
        gt(@name_length, 12) -> @name = substring(#firstname, 9)
        length(@name) == 9 -> @name = concat(@name, "...")
        print("Welcome $.variables.name")
    ]
```

This csvpath does backflips to get a truncated name, mainly proving that CsvPath is not a programming language. Validation is enough.


