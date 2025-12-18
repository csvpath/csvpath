
## none()

A value producer and line() schema type representing a None value.

| Data signatures                                  |
|:-------------------------------------------------|
| none()                                           |
| none( nullable: $${\color{green}None}$$ )        |
| none( header reference: $${\color{green}str}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                   |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| none()                                                                                                                                                                                                                                                                                                                                                            |
| none( nullable: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |
| none( header reference: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )                                                                                                                                                                                                                                                              |

| Purpose    | Value                                                  |
|:-----------|:-------------------------------------------------------|
| Main focus | none() produces a calculated value and decides matches |
| Type       | None is a line() schema type                           |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


