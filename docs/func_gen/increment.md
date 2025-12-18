
Increment
increment() increases a variable tracking each match every N-matches.

For example in a file with four lines of first names where there are
two Johns, one Fred, and one Shen we would expect
increment.john(#firstname=="John", 2) to create the variable
john_increment with a value of 1.

increment(), counter(), and every() are similar. counter() lets you
add N each time a match component evaluates to True. increment() adds
1 each N times a match component evaluates to True. every() adds 1
every N-times a value is seen, matching or not.

| Data signatures                               |
|:----------------------------------------------|
| increment( Match component: [36m[3mAny[0m, Ratio: [36m[3mint[0m ) |

| Call signatures                                      |
|:-----------------------------------------------------|
| increment( Match component: [36m[3mMatchable[0m, Ratio: [36m[3mTerm[0m ) |

| Purpose    | Value                                   |
|:-----------|:----------------------------------------|
| Main focus | increment() produces a calculated value |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | [36m[3monmatch[0m             |
| Value qualifiers | [36m[3monmatch[0m             |
| Name qualifier   | [36m[3moptionally expected[0m |


