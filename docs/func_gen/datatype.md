
Datatype
datatype() returns the best fitting type for a header value on a given line.
              String is considered the least specific type, meaning that a type is only
              considered a string if all other types do not match. For example, "" is
              considered a none() match and "false" is considered a boolean() match.
            

| Data signatures                  |
|:---------------------------------|
| datatype( header of value: [36m[3mstr[0m ) |

| Call signatures                                       |
|:------------------------------------------------------|
| datatype( header of value: [36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m ) |

| Purpose    | Value                                  |
|:-----------|:---------------------------------------|
| Main focus | datatype() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


