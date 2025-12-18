
Push

Appends a value to a stack variable. The stack is created if not
found.

If the distinct qualifier is used, the value to be pushed is ignored
if it is already present in the stack. Adding the notnone qualifier
prevents push() from adding a None to the stack.

| Data signatures                                   |
|:--------------------------------------------------|
| push( new stack name: str )                       |
| push( stack name: str|list, push this: None|Any ) |

| Call signatures                                                                                                 |
|:----------------------------------------------------------------------------------------------------------------|
| push( new stack name: Term )                                                                                    |
| push( stack name: Term|Variable|Header|Function|Reference, push this: Term|Variable|Header|Function|Reference ) |

| Purpose    | Value                   |
|:-----------|:------------------------|
| Main focus | push() is a side-effect |

| Context          | Qualifier                            |
|:-----------------|:-------------------------------------|
| Match qualifiers | onmatch, distinct, notnone, skipnone |
| Value qualifiers | onmatch                              |


