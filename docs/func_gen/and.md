
And
 and() tests if its contained match components evaluate to True.

Matching is ANDed by default, but it can be set to OR. And and() gives
you a bit more control in certain situations, such as making. a
when/do expression that is based on multiple match components.

The functionality of and() overlaps with all(), but all() has powers
that are more specific than and().

| Data signatures                                          |
|:---------------------------------------------------------|
| and( Eval this: [36m[3mNone[0m|[36m[3mAny[0m, And eval this: [36m[3mNone[0m|[36m[3mAny[0m, ... ) |

| Call signatures                                            |
|:-----------------------------------------------------------|
| and( Eval this: [36m[3mMatchable[0m, And eval this: [36m[3mMatchable[0m, ... ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | and() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


