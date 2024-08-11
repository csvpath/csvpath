
# Total Lines

The `total_lines()` function returns the total count of lines in the file being scanned. It is a 1-based count, so the header row is row 0 but represents a count of 1. In most cases, csvpaths use 0-based counts, e.g. the header indexes. However, for convenient access, this function is returning a count, not an index. The first line is at the 0th index.


