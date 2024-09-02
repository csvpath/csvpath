
# After Blank

`after_blank()` matches when the current line was preceded by a line with no values.

Bear in mind a few things:
- By default CsvPath skips truly blank lines
- Lines with delimiters but no data are not exactly blank
- Lines with fewer than the expected number of headers aren't blank

This function considers:
- The physical lines in the file
- The possibility of delimiters but no values

Basically, if the preceding line had no data in any header or no characters at all (or only whitespace characters), `after_blank()` would return True.

`after_blank()` takes no arguments and always returns a bool value.

