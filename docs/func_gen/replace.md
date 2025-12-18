
## replace()

Replace

Replaces the value of the header with another value on every line.

If a header is passed as the first argument its value is replaced.

If a header name or index is passed as the first argument the
identified header's value is replaced.

For example, $[*][@a = line_number() replace(#order_number, @a)]

| Data signatures                                                           |
|:--------------------------------------------------------------------------|
| replace( replace value: None ǁ Any, replacement: Any )                    |
| replace( replace by header identity: int ǁ str, replacement: None ǁ Any ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| replace( replace value: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header), replacement: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) )          |
| replace( replace by header identity: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), replacement: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | replace() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


