Get
Returns a variable's tracking or index value. The variable is either:
- found by name using string value of the first argument, or - a
variable or reference that is a dictionary or stack

A tracking value is similar to a dictionary key, usually keying a
count, calculation, or transformation.

An index is the 0-based position number of an item in a stack
variable. Stack variables are like lists or tuples.

While get() and put() make it possible to create and use tracking-
value variables in an ad hoc dict-like way, this is not recommended
unless there is no simplier solution based on more specific functions.
| Data signatures                                                                                                |
|:---------------------------------------------------------------------------------------------------------------|
| get( var name: [36m[3mstr[0m|[36m[3mdict[0m, [tracking value: [36m[3mNone[0m|[36m[3mstr[0m|[36m[3mint[0m|[36m[3mfloat[0m|[36m[3mbool[0m|[36m[3m''[0m], [default: [36m[3mNone[0m|[36m[3mstr[0m|[36m[3mint[0m|[36m[3mfloat[0m|[36m[3mbool[0m|[36m[3m''[0m] ) |
| Call signatures                                                                                                                                     |
|:----------------------------------------------------------------------------------------------------------------------------------------------------|
| get( var name: [36m[3mHeader[0m|[36m[3mTerm[0m|[36m[3mFunction[0m|[36m[3mVariable[0m|[36m[3mReference[0m, [tracking value: [36m[3mHeader[0m|[36m[3mTerm[0m|[36m[3mFunction[0m|[36m[3mVariable[0m], [default: [36m[3mHeader[0m|[36m[3mTerm[0m|[36m[3mFunction[0m|[36m[3mVariable[0m] ) |
| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | get() produces a calculated value |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
