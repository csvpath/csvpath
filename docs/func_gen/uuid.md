
## uuid()

A line() schema type indicating that the value must be a UUID

As a type, this function will always match empty values unless you use the notnone qualifier.

| Data signatures                                                               |
|:------------------------------------------------------------------------------|
| uuid()                                                                        |
| uuid( value to check: $${\color{green}str}$$ ǁ $${\color{green}None}$$ ǁ '' ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| uuid()                                                                                                                                                                                                                                                                                                                                                                  |
| uuid( value to check: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ) |

| Purpose    | Value                            |
|:-----------|:---------------------------------|
| Main focus | uuid() determines if lines match |
| Type       | Uuid is a line() schema type     |

| Context          | Qualifier                                                                                                                                                                                                                                                                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [notnone](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#notnone), [distinct](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#distinct)                                                                       |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [notnone](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#notnone) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
