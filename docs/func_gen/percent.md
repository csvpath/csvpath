
Percent
Returns the percent of scanned, matched or all lines so-far seen of
the total data lines in the file. Data lines have data. The total does
not include blanks.

By default percent() tracks % matches of total lines in the file. If
percent() has the onmatch qualifier it always tracks matches,
overriding

| Data signatures                      |
|:-------------------------------------|
| percent( scan, match, or line: [36m[3mstr[0m ) |

| Call signatures                       |
|:--------------------------------------|
| percent( scan, match, or line: [36m[3mTerm[0m ) |

| Purpose    | Value                                 |
|:-----------|:--------------------------------------|
| Main focus | percent() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


