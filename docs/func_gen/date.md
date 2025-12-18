
## date()

date() has two purposes.

First, it may indicate that a value must be a {self.name} to be valid. To do this, it must be an argument to a line() and have a header argument.

Alternatively, it may generate a date from a string. Generally, {self.name}() recognizes {self.name}s without needing a format string.

| Data signatures                                                                                         |
|:--------------------------------------------------------------------------------------------------------|
| date( date: $${\color{green}None}$$ ǁ $${\color{green}datetime}$$ ǁ $${\color{green}date}$$ )           |
| date( date string: $${\color{green}None}$$ ǁ $${\color{green}str}$$, [format: $${\color{green}str}$$] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| date( date: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) )                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| date( date string: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), [format: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference)] ) |

| Purpose    | Value                                                  |
|:-----------|:-------------------------------------------------------|
| Main focus | date() produces a calculated value and decides matches |
| Type       | Date is a line() schema type                           |

| Context          | Qualifier                                                                                                                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [notnone](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#notnone), [strict](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#strict), [distinct](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#distinct) |
| Value qualifiers | onmatch, notnone                                                                                                                                                                                                                                                                                                                               |


