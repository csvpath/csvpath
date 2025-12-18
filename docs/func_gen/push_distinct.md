Push distinct
Appends a value to a stack variable. The stack is created if not
found.

If the distinct qualifier is used, the value to be pushed is ignored
if it is already present in the stack. Adding the notnone qualifier
prevents push() from adding a None to the stack.
| Data signatures                                            |
|:-----------------------------------------------------------|
| push_distinct( new stack name: [36m[3mstr[0m )                       |
| push_distinct( stack name: [36m[3mstr[0m|[36m[3mlist[0m, push this: [36m[3mNone[0m|[36m[3mAny[0m ) |
| Call signatures                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------|
| push_distinct( new stack name: [36m[3mTerm[0m )                                                                                    |
| push_distinct( stack name: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, push this: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |
| Purpose    | Value                            |
|:-----------|:---------------------------------|
| Main focus | push_distinct() is a side-effect |
| Context          | Qualifier                            |
|:-----------------|:-------------------------------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3mdistinct[0m, [36m[3mnotnone[0m, [36m[3mskipnone[0m |
| Value qualifiers | [36m[3monmatch[0m                              |
