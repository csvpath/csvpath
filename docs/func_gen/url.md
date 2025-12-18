
## url()

A line() schema type indicating that the value it represents must be an URL

| Data signatures                                                   |
|:------------------------------------------------------------------|
| url( url: $${\color{green}str}$$ ǁ $${\color{green}None}$$ ǁ '' ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                             |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| url( url: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | url() determines if lines match |
| Type       | Url is a line() schema type     |

| Context          | Qualifier                                                                                                                                                                                                                                                    |
|:-----------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [notnone](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#notnone), [distinct](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#distinct) |
| Value qualifiers | onmatch, notnone                                                                                                                                                                                                                                             |


