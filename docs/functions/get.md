
# Get

`get()` returns the value of a variable. It can access tracking values and stack indexes.

If the first argument is a variable we expect a second argument pointing to a tracking value key or a stack index. Otherwise, we find the variable by name.

If there is a second argument then the variable must be either a dictionary or a list. In CsvPaths terminology, a variable with tracking values or a stack.

If any reference doesn't work -- i.e. the variable isn't found or the tracking value or index doesn't exist -- the return is None. A warning will be logged.

## Examples

```bash
            $[1*][
                tally(#firstname)
                @john = get(@firstname, "John")
                @john == 2 -> print("We have seen $.variables.john humans")
            ]
```

This contrived csvpath creates a tally of `#firstname`. The `@john` variable pulls the tally count keyed by the "John" tracking value. When the count hits `2` we print a message.

