
## header_name()

Header name

Looks up a header name by index. e.g. header_name(0, "firstname")
returns True if the first header is "firstname".

If given an expected result as a 2nd argument the return is True/False
on the match of expected to actual

If no value is provided, header_name() is an existance test for the
header, not a check for the line having a value for the header.

| Data signatures                                                                                                                                       |
|:------------------------------------------------------------------------------------------------------------------------------------------------------|
| header_name( header identity: $${\color{green}str}$$ ǁ $${\color{green}int}$$, [value check: $${\color{green}None}$$ ǁ $${\color{green}Any}$$ ǁ ''] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                 |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| header_name( header identity: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable), [value check: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)] ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | header_name() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |


