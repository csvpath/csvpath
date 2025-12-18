
## mismatch()

Mismatch

mismatch() returns the number of headers in a row greater or less than
the number expected. CsvPath uses the 0th row as headers; although,
you can reset the headers at any point.

Headers are like columns, except without any of the guarantees:

- Expected headers may be missing from any given line

- The number of headers per file is not fixed

- There can be multiple header rows

- The header line may not be the 0th line

- Some lines can be blank and have no "cells" so no headers apply

When the designated headers -- usually those set from the first non-
blank line -- do not match the number of values in a row there is a
mismatch. The number of values means data values plus the empty string
for those values that have a position in the line but no more
substantial content.

mismatch() counts the number of values, including blanks, compares
that number to the number of headers, and returns the difference as a
positive or signed integer.

By default mismatch() returns the absolute value of the difference. If
you pass a negative boolean (including "false", false(), and no()) or
"signed" then mismatch() returns a negative number if the line has
fewer delimited values than the current headers.

If a line has no delimiters but does have whitespace characters it
technically has one header. mismatch() doesn't give credit for the
whitespace because in reality the line is blank and has zero headers.

| Data signatures                                       |
|:------------------------------------------------------|
| mismatch()                                            |
| mismatch( a literal: signed: $${\color{green}str}$$ ) |
| mismatch( signed: $${\color{green}bool}$$ )           |

| Call signatures                                                                                           |
|:----------------------------------------------------------------------------------------------------------|
| mismatch()                                                                                                |
| mismatch( a literal: signed: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |
| mismatch( signed: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )            |

| Purpose    | Value                                  |
|:-----------|:---------------------------------------|
| Main focus | mismatch() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |


