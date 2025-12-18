
## insert()

Inserts a new header-value at a certain position within the output
data.

For e.g.: insert(3, @critter)

This match component creates a new header at index 3 (0-based) and
sets the value for each line of output to the @critter variable.



| Data signatures                                                           |
|:--------------------------------------------------------------------------|
| insert( insert at index: int, insert header name: str, data: None ǁ Any ) |

| Call signatures                                                                                           |
|:----------------------------------------------------------------------------------------------------------|
| insert( insert at index: Term, insert header name: Term, data: Variable ǁ Header ǁ Function ǁ Reference ) |

| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | insert() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


