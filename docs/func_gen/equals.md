Equals
Tests the equality of two values.

In most cases you will use == to test equality. However, in some cases
equals() gives more flexibility.

Moreover, in one case, you must use the function, not ==. Using
equals() is required in order to set a variable to the value of an
equality test.

In other words, to set @a equal to the equality test of @b to the
string "c", you must do: @a = equals(@b, "c"). @a = @b == "c" is not
allowed.
| Data signatures                            |
|:-------------------------------------------|
| equals( is this: [36m[3mAny[0m, equal to that: [36m[3mAny[0m ) |
| Call signatures                                                                                                    |
|:-------------------------------------------------------------------------------------------------------------------|
| equals( is this: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, equal to that: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |
| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | equals() determines if lines match |
| Aliases    | equal, equals, eq                  |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
