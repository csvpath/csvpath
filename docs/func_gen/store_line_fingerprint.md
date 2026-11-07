
## store_line_fingerprint()

Migrates a by-line fingerprint from its variable into run metadata. If
a name qualifier was used to create the by-line fingerprint the same
name must be used with this function.

| Data signatures          |
|:-------------------------|
| store_line_fingerprint() |

| Call signatures          |
|:-------------------------|
| store_line_fingerprint() |

| Purpose                | Value                                     |
|:-----------------------|:------------------------------------------|
| Main focus             | store_line_fingerprint() is a side-effect |
| Has internal variables | False                                     |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                                                                                                                                                                            |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
