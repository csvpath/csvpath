
## and()

and() tests if its contained match components evaluate to True.

Matching is ANDed by default, but it can be set to OR. And and() gives
you a bit more control in certain situations, such as making. a
when/do expression that is based on multiple match components.

The functionality of and() overlaps with all(), but all() has powers
that are more specific than and().

| Data signatures                                              |
|:-------------------------------------------------------------|
| and( Eval this: None ǁ Any, And eval this: None ǁ Any, ... ) |

| Call signatures                                            |
|:-----------------------------------------------------------|
| and( Eval this: Matchable, And eval this: Matchable, ... ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | and() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


