
## email()

A line() schema type indicating that the value it represents must be an email

| Data signatures                                                         |
|:------------------------------------------------------------------------|
| email( address: $${\color{green}str}$$ ǁ $${\color{green}None}$$ ǁ '' ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                   |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| email( address: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | email() determines if lines match |
| Type       | Email is a line() schema type     |

| Context          | Qualifier                                                                                                                                                                                                                                                    |
|:-----------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [notnone](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#notnone), [distinct](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#distinct) |
| Value qualifiers | onmatch, notnone                                                                                                                                                                                                                                             |


