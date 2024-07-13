
# No

Always returns False to matches() and to_value(). Useful for turning off matches for testing or other reasons and/or collecting variables without matching.

## Example

    $file.csv[*][@counting=count_lines() no()]

This path never matches but does set `counting` to the current line number.



