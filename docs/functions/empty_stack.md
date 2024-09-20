
# Empty Stack

The `empty_stack()` function collects the names of empty values. Its primary job is identifying headers without values. However, it can also check on variables.

`empty_stack()` without arguments scans all the headers for values and creates a stack of the names of any that are empty. You can provide any number of arguments to `empty_stack()` to narrow its search down to just those values, both headers and variables.


## Example

```bash
    $file.csv[*][
        push("empties", empty_stack())
        last() -> var_table("empties")
    ]
```

This csvpath creates an `empties` variable that is a stack of stacks. Each item in the `empties` stack represents the empty headers in a line. The result might look like:

┌───────────────────────────┐
│ empties                   │
├───────────────────────────┤
│ ['firstname', 'lastname'] │
├───────────────────────────┤
│ ['firstname']             │
├───────────────────────────┤
│ ['lastname']              │
├───────────────────────────┤
│ []                        │
└───────────────────────────┘


