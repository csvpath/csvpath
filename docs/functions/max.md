
# Max and Min

These functions compare the values of a header across rows. Values are compared as numbers or bools, when possible; otherwise, lexicographically.

The comparisons are to scanned or matched rows or to all rows. The choice is indicated by a second argument of "scan", "match", or "line". If no second argument is provided, all rows are compared.

When values are compared as strings they are lower-cased, trimmed, and compared using `<` and `>`.

If a header is used to find the value there are two behaviors:
- If the header is a name and the line count is 0 and the name matches the value the row is skipped
- If the header is an index the row is always considered

## Example

    $file.csv[*][@the_max = max.ages(#age, "scan")]

This path collects the ages in the `ages` variable under scan count keys and assigns the max to the `max` variable.

    $file.csv[*][@the_max = max.ages(#age)]

This path collects the ages in the `ages` variable under line count keys and assigns the max to the `max` variable.


