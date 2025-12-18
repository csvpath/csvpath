
## increment()

increment() increases a variable tracking each match every N-matches.

For example in a file with four lines of first names where there are
two Johns, one Fred, and one Shen we would expect
increment.john(#firstname=="John", 2) to create the variable
john_increment with a value of 1.

increment(), counter(), and every() are similar. counter() lets you
add N each time a match component evaluates to True. increment() adds
1 each N times a match component evaluates to True. every() adds 1
every N-times a value is seen, matching or not.

| Data signatures                                                                     |
|:------------------------------------------------------------------------------------|
| increment( Match component: $${\color{green}Any}$$, Ratio: $${\color{green}int}$$ ) |

| Call signatures                                                                                                            |
|:---------------------------------------------------------------------------------------------------------------------------|
| increment( Match component: Matchable, Ratio: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |

| Purpose    | Value                                   |
|:-----------|:----------------------------------------|
| Main focus | increment() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |
| Name qualifier   | optionally expected                                                                |


