
## insert()

Inserts a new header-value at a certain position within the output
data.

For e.g.: insert(3, @critter)

This match component creates a new header at index 3 (0-based) and
sets the value for each line of output to the @critter variable.



| Data signatures                                                                                                                                       |
|:------------------------------------------------------------------------------------------------------------------------------------------------------|
| insert( insert at index: $${\color{green}int}$$, insert header name: $${\color{green}str}$$, data: $${\color{green}None}$$ ǁ $${\color{green}Any}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| insert( insert at index: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), insert header name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), data: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |

| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | insert() is a side-effect |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
