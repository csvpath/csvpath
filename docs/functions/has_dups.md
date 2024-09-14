
# Dup Lines, Has Dups, and Count Dups

These functions are tools for tracking duplicate lines.

- `has_dups()` matches any row with one or more duplicates
- `count_dups()` returns the number of duplicates of the current line
- `dup_lines()` returns a stack of line numbers of duplicates to the current line (not including the current line number)

While `dup_lines()`'s main job is providing access to the list of duplicate lines, it can also determine if a line matches, when used alone.

The dup functions can take one or more headers to find the duplicate rows based only on those values. When no arguments are given they compares the entire row for duplicates.

The dups functions can take the `onmatch` qualifier. You can use a name qualifier, i.e. any word that is not the name of one of the built-in qualifiers, to name the tracking variable the functions use to track duplicates. This allows you to track multiple sets of duplicates using different combinations of headers.


## Example

```bash
    $test[*][
        @d = dup_lines(#1)
        dup_lines(#1) -> print("line $.line_count has dups in $.variables.dups")
    ]
```

This path prints every time a duplicate is found. The print string includes the list of line numbers that duplicate the current row.


