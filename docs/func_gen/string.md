
## string()

String

string() indicates that a value must be a string to be valid. All CSV
values start as strings so this function can be expected to return
True                unless there is a notnone or length constraint
violation.

To set a min length without setting a max length use a none() argument
for max. E.g. to set a string of length greater than or equal to 5 do:
string(none(), 5).

| Data signatures                                                  |
|:-----------------------------------------------------------------|
| string( value: str ǁ None ǁ '', [max len: int], [min len: int] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| string( value: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), [max len: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)], [min len: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)] ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | string() determines if lines match |
| Type       | String is a line() schema type     |

| Context          | Qualifier                  |
|:-----------------|:---------------------------|
| Match qualifiers | onmatch, notnone, distinct |
| Value qualifiers | onmatch                    |


