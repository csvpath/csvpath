
## dup_lines()

dups_lines() returns a list of the numbers of duplicate lines or lines
with duplicate subsets of header values.

| Data signatures                                                             |
|:----------------------------------------------------------------------------|
| dup_lines( [check: $${\color{green}None}$$ ǁ $${\color{green}Any}$$], ... ) |

| Call signatures                                                                                           |
|:----------------------------------------------------------------------------------------------------------|
| dup_lines( [check: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header)], ... ) |

| Purpose                | Value                                   |
|:-----------------------|:----------------------------------------|
| Main focus             | dup_lines() produces a calculated value |
| Has internal variables | True                                    |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                                                                                                                                                                            |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
