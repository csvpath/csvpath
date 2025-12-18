
## header_index()

Header index

Looks up a header index by header name. e.g. header_index("firstname")
returns 0 when the "firstname" header is first.
header_index("lastname", 1) returns True if the "lastname" header is
second.

If given an expected result as a 2nd argument the return is True/False
on the match of expected to actual

If no value is provided, header_index() is an existance test for the
header, not a check for the line having a value for the header.

| Data signatures                                                                                                                                        |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------|
| header_index( header identity: $${\color{green}str}$$ ǁ $${\color{green}int}$$, [value check: $${\color{green}None}$$ ǁ $${\color{green}Any}$$ ǁ ''] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                  |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| header_index( header identity: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable), [value check: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)] ) |

| Purpose    | Value                                      |
|:-----------|:-------------------------------------------|
| Main focus | header_index() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


