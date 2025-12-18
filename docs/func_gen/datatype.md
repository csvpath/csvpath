
## datatype()

datatype() returns the best fitting type for a header value on a given line.
              String is considered the least specific type, meaning that a type is only
              considered a string if all other types do not match. For example, "" is
              considered a none() match and "false" is considered a boolean() match.
            

| Data signatures                  |
|:---------------------------------|
| datatype( header of value: str ) |

| Call signatures                                                                                                                                                                                             |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| datatype( header of value: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ) |

| Purpose    | Value                                  |
|:-----------|:---------------------------------------|
| Main focus | datatype() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


