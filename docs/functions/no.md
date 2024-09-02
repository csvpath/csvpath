
# Yes, No and None

These functions simply returns True or False or None. A csvpath like `$[*][yes()]` always matches every line. One like `$[*][no()]` never matches.

They are most useful for turning off matches for testing, or for other reasons, and/or collecting variables without matching.

`yes()` and `no()` are aliased with `true()` and `false()`.

## Example

```bash
    $file.csv[*][@counting=count_lines() no()]
```

This path never matches but it does set `counting` to the current line number as each line is scanned.



