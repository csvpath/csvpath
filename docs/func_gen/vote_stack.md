
Vote stack
Returns the votes of the match components for each line as a stack.

The votes are collected from the central record, not from each
component directly. This means that any match components that have not
yet voted will return None, rather than True or False. This is most
noticable when you are printing the vote stack. The print function,
not having voted until it is complete, always returns None.

| Purpose    | Value                         |
|:-----------|:------------------------------|
| Main focus | vote_stack() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


