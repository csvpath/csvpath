
Range
Returns true if the values provided have a between relationship.

The values can be dates, numbers, or strings. They must all be of the
same type.

between() has a number of aliases. One of them may work better
syntactically in your use case, but they are all the same logic.

| Data signatures                                                                                  |
|:-------------------------------------------------------------------------------------------------|
| range( The value to test: [36m[3mNone[0m|[36m[3mdatetime[0m|[36m[3mdate[0m, From: [36m[3mNone[0m|[36m[3mdatetime[0m|[36m[3mdate[0m, To: [36m[3mNone[0m|[36m[3mdatetime[0m|[36m[3mdate[0m ) |
| range( The value to test: [36m[3mNone[0m|[36m[3mfloat[0m|[36m[3mint[0m, From: [36m[3mNone[0m|[36m[3mfloat[0m|[36m[3mint[0m, To: [36m[3mNone[0m|[36m[3mfloat[0m|[36m[3mint[0m )             |
| range( The value to test: [36m[3mNone[0m|[36m[3mstr[0m, From: [36m[3mNone[0m|[36m[3mstr[0m, To: [36m[3mNone[0m|[36m[3mstr[0m )                               |

| Call signatures                                                                                                                                                 |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| range( The value to test: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, From: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, To: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |
| range( The value to test: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, From: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, To: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |
| range( The value to test: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, From: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, To: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | range() determines if lines match |
| Aliases    | between, inside, from_to, range   |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


