
Push distinct

Appends a value to a stack variable. The stack is created if not
found.

If the distinct qualifier is used, the value to be pushed is ignored
if it is already present in the stack. Adding the notnone qualifier
prevents push() from adding a None to the stack.

| Data signatures                                                |
|:---------------------------------------------------------------|
| push_distinct( new stack name: str )                           |
| push_distinct( stack name: str ǁ list, push this: None ǁ Any ) |

| Call signatures                                                                                                                          |
|:-----------------------------------------------------------------------------------------------------------------------------------------|
| push_distinct( new stack name: Term )                                                                                                    |
| push_distinct( stack name: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, push this: Term ǁ Variable ǁ Header ǁ Function ǁ Reference ) |

| Purpose    | Value                            |
|:-----------|:---------------------------------|
| Main focus | push_distinct() is a side-effect |

| Context          | Qualifier                            |
|:-----------------|:-------------------------------------|
| Match qualifiers | onmatch, distinct, notnone, skipnone |
| Value qualifiers | onmatch                              |


