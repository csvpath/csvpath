
Boolean
boolean() is a line() schema type representing a bool value.
To generate a particular bool value use yes() or no().
As you would think, setting distinct limits the number of lines to
            four, for practical purposes. Namely: yes(), no(), none(), and a header
            name.

| Data signatures                 |
|:--------------------------------|
| boolean( value: [36m[3mNone[0m|[36m[3mbool[0m|[36m[3mstr[0m ) |

| Call signatures                                 |
|:------------------------------------------------|
| boolean( value: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m ) |

| Purpose    | Value                                                     |
|:-----------|:----------------------------------------------------------|
| Main focus | boolean() produces a calculated value and decides matches |
| Type       | Boolean is a line() schema type                           |

| Context          | Qualifier         |
|:-----------------|:------------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3mdistinct[0m |
| Value qualifiers | [36m[3monmatch[0m, [36m[3mnotnone[0m  |


