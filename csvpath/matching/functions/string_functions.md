
# String Functions

The string handling functions behave much like their Python equivalents.

### concat(value, value, ...)

### length(value)

### lower(value)

### strip(value)

### substring(value, int)

### upper(value)

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


