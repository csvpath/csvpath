
## peek()

Returns a value at a stack variable index, but does not remove it.

The stack is created if not found.

| Data signatures                     |
|:------------------------------------|
| peek( stack name: str, index: int ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| peek( stack name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), index: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | peek() produces a calculated value |

| Context          | Qualifier       |
|:-----------------|:----------------|
| Match qualifiers | onmatch, asbool |
| Value qualifiers | onmatch         |


