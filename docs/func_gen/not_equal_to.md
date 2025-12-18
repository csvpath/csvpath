Not equal to
Tests the equality of two values.

In most cases you will use == to test equality. However, in some cases
not_equal_to() gives more flexibility.

Moreover, in one case, you must use the function, not ==. Using
not_equal_to() is required in order to set a variable to the value of
an equality test.

In other words, to set @a equal to the equality test of @b to the
string "c", you must do: @a = not_equal_to(@b, "c"). @a = @b == "c" is
not allowed.
| Data signatures                                  |
|:-------------------------------------------------|
| not_equal_to( is this: [36m[3mAny[0m, equal to that: [36m[3mAny[0m ) |
| Call signatures                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------|
| not_equal_to( is this: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, equal to that: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |
| Purpose    | Value                                    |
|:-----------|:-----------------------------------------|
| Main focus | not_equal_to() determines if lines match |
| Aliases    | neq, not_equal_to                        |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
