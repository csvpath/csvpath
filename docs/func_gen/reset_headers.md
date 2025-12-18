
## reset_headers()

Reset headers

reset_headers() sets the headers to the values of the current row.

This may change the number of headers. It may be that the header names
are completely different after the reset.

Resetting headers has no effect on the lines that have already been
passed.

If a function is passed as an argument it is evaluated after the
header reset happens as a side-effect.

To keep track of resets, give reset_headers() a name qualifier. E.g.
reset_headers.myreset(). You can then look at the value of
@myreset_count to see the number of times that reset_headers() match
component was called. And you can look at @myreset_lines to see the
line numbers where the reset calls happened.

| Data signatures                    |
|:-----------------------------------|
| reset_headers( [evaluate this: ] ) |

| Call signatures                                                                                                      |
|:---------------------------------------------------------------------------------------------------------------------|
| reset_headers( [evaluate this: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function)] ) |

| Purpose    | Value                            |
|:-----------|:---------------------------------|
| Main focus | reset_headers() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


