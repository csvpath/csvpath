String
string() indicates that a value must be a string to be valid. All CSV
values start as strings so this function can be expected to return
True                unless there is a notnone or length constraint
violation.

To set a min length without setting a max length use a none() argument
for max. E.g. to set a string of length greater than or equal to 5 do:
string(none(), 5).
| Data signatures                                              |
|:-------------------------------------------------------------|
| string( value: [36m[3mstr[0m|[36m[3mNone[0m|[36m[3m''[0m, [max len: [36m[3mint[0m], [min len: [36m[3mint[0m] ) |
| Call signatures                                                                       |
|:--------------------------------------------------------------------------------------|
| string( value: [36m[3mHeader[0m|[36m[3mVariable[0m|[36m[3mFunction[0m|[36m[3mReference[0m, [max len: [36m[3mTerm[0m], [min len: [36m[3mTerm[0m] ) |
| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | string() determines if lines match |
| Type       | String is a line() schema type     |
| Context          | Qualifier                  |
|:-----------------|:---------------------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3mnotnone[0m, [36m[3mdistinct[0m |
| Value qualifiers | [36m[3monmatch[0m                    |
