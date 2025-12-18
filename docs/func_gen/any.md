Any
any() returns True if at least one contained match component matches a
given value.

With no arguments any() matches if there are values in any variable or
header.

With a single headers() or variables() function any() returns True if
there is a match component of the the type indicated with a value.

With a second argument the test is for the specific value in any match
component of the indicated type.

any() is similar to or() or OR logic. While any() gives you more fine-
grained control, remember that you can also use logic-mode to
configure a csvpath to use OR as the basis for matching.
| Data signatures                                         |
|:--------------------------------------------------------|
| any()                                                   |
| any( where to look: [36m[3mNone[0m|[36m[3mAny[0m, value to find: [36m[3mNone[0m|[36m[3mAny[0m ) |
| any( where to look: [36m[3mNone[0m|[36m[3mAny[0m )                          |
| Call signatures                                                                                          |
|:---------------------------------------------------------------------------------------------------------|
| any()                                                                                                    |
| any( where to look: [36m[3mVariables[0m|[36m[3mHeaders[0m, value to find: [36m[3mTerm[0m|[36m[3mFunction[0m|[36m[3mHeader[0m|[36m[3mVariable[0m|[36m[3mReference[0m|[36m[3mEquality[0m ) |
| any( where to look: [36m[3mVariables[0m|[36m[3mHeaders[0m|[36m[3mTerm[0m|[36m[3mFunction[0m|[36m[3mHeader[0m|[36m[3mVariable[0m|[36m[3mReference[0m|[36m[3mEquality[0m )                 |
| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | any() determines if lines match |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
