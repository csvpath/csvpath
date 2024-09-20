
# Get and Put

## `get()`

`get()` returns the value of a variable. It can access tracking values and stack indexes. Note that this function is important in a few cases but generally duplicates the ability to use `@varname.tracking` syntax.

The variable access by `get()` is dynamic. If you pass a term, e.g. "my_var", you access the named variable. Likewise, if you pass a header, the value of the header names the variable `get()` retrieves.

If there is a second argument then the variable must be either a dictionary or a list. In CsvPaths terminology, a variable with tracking values or a stack.

If any reference doesn't work -- i.e. the variable isn't found or the tracking value or index doesn't exist -- the return is None. A warning will be logged.

## `put()`

`put()` lets you set a variable dynamically. It's most important use is for setting tracking values.

The syntax is `put(varname, value)` or `put(varname, tracking_key, tracking_value)`. The names and values are dynamic. This means that the name of the value could be the value of a header or another variable. If the variable doesn't exist it will be created.

## Examples

```bash
            $[1*][
                tally(#firstname)
                @john = get("tally_firstname", "John")
                @john == 2 -> print("We have seen $.variables.john humans")
            ]
```

This contrived csvpath creates a tally of `#firstname`. The `@john` variable pulls the tally count keyed by the "John" tracking value. When the count hits `2` we print a message.

