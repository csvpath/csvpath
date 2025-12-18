
Insert
Inserts a new header-value at a certain position within the output
data.

For e.g.: insert(3, @critter)

This match component creates a new header at index 3 (0-based) and
sets the value for each line of output to the @critter variable.



| Data signatures                                                         |
|:------------------------------------------------------------------------|
| insert( insert at index: [36m[3mint[0m, insert header name: [36m[3mstr[0m, data: [36m[3mNone[0m|[36m[3mAny[0m ) |

| Call signatures                                                                                     |
|:----------------------------------------------------------------------------------------------------|
| insert( insert at index: [36m[3mTerm[0m, insert header name: [36m[3mTerm[0m, data: [36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |

| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | insert() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


