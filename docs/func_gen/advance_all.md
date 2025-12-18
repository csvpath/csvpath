
## advance_all()

Like advance(), advance_all() jumps processing N-lines forward. The
lines skipped will not be considered or collected as matched or
unmatched.

advance_all() has the additional functionality of advancing all
csvpaths running breadth-first.

Csvpaths running breadth-first are in a named-paths group run that was
started using the collect_by_line(), fast_forward_by_line(), or
next_by_line() methods on the CsvPaths class.

advance_all() is similar to skip(). Acting in just one csvpath, skip()
cuts-short the processing of its line and jumps to the next line.
advance_all(), like advance(), finishes the line it is on within its
csvpath before jumping over the next N-lines.

However, similar to skip(), advance_all() stops the line it is
evaluated on from being fully considered because in a breadth-first
run each csvpath evaluates a line before the next line is started.
advance_all() prevents downstream csvpaths from seeing the line.

For example, take two csvpaths in a named-paths group that was run
using fast_forward_by_line(). If the first csvpath uses a when/do
operator to evaluate advance_all() on the odd lines, the second
csvpath will only see the even lines.

| Data signatures                                         |
|:--------------------------------------------------------|
| advance_all( lines to advance: $${\color{green}int}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                       |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| advance_all( lines to advance: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ) |

| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | advance_all() is a side-effect |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |


