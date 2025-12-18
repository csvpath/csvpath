
Push

Appends a value to a stack variable. The stack is created if not
found.

If the distinct qualifier is used, the value to be pushed is ignored
if it is already present in the stack. Adding the notnone qualifier
prevents push() from adding a None to the stack.

| Data signatures                                   |
|:--------------------------------------------------|
| push( new stack name: str )                       |
| push( stack name: strǁlist, push this: NoneǁAny ) |

| Call signatures                                                                                                 |
|:----------------------------------------------------------------------------------------------------------------|
| push( new stack name: Term )                                                                                    |
| push( stack name: TermǁVariableǁHeaderǁFunctionǁReference, push this: TermǁVariableǁHeaderǁFunctionǁReference ) |

| Purpose    | Value                   |
|:-----------|:------------------------|
| Main focus | push() is a side-effect |

| Context          | Qualifier                            |
|:-----------------|:-------------------------------------|
| Match qualifiers | onmatch, distinct, notnone, skipnone |
| Value qualifiers | onmatch                              |


