
## push_distinct()

Appends a value to a stack variable. The stack is created if not
found.

If the distinct qualifier is used, the value to be pushed is ignored
if it is already present in the stack. Adding the notnone qualifier
prevents push() from adding a None to the stack.

| Data signatures                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------|
| push_distinct( new stack name: $${\color{green}str}$$ )                                                                 |
| push_distinct( stack name: $${\color{green}str}$$ ǁ list, push this: $${\color{green}None}$$ ǁ $${\color{green}Any}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| push_distinct( new stack name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| push_distinct( stack name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), push this: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |

| Purpose    | Value                            |
|:-----------|:---------------------------------|
| Main focus | push_distinct() is a side-effect |

| Context          | Qualifier                            |
|:-----------------|:-------------------------------------|
| Match qualifiers | onmatch, distinct, notnone, skipnone |
| Value qualifiers | onmatch                              |


