
## nor()

nor() tests if its contained match components are all False.

nor() is the inverse of and(). Matching is ANDed by default. Like
and() nor() helps simplify expressions, in this case by minimizing the
number of not() functions needed.

| Data signatures                                                                                                                          |
|:-----------------------------------------------------------------------------------------------------------------------------------------|
| nor( Eval this: $${\color{green}None}$$ ǁ $${\color{green}Any}$$, And eval this: $${\color{green}None}$$ ǁ $${\color{green}Any}$$, ... ) |

| Call signatures                                            |
|:-----------------------------------------------------------|
| nor( Eval this: Matchable, And eval this: Matchable, ... ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | nor() determines if lines match |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
