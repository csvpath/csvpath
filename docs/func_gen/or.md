Or
or() implements OR logic in a csvpath writer-directed way.

Evaluation of or() completes before any errors are handled to allow
for the OR operation to be informed by branch invalidity.

Remember that logic-mode allows you to apply OR logic to the whole
csvpath, if that is needed. or() is of course more specific and
composable.
| Data signatures                                                    |
|:-------------------------------------------------------------------|
| or( First alternative: [36m[3mNone[0m|[36m[3mAny[0m, Next alternative: [36m[3mNone[0m|[36m[3mAny[0m, ... ) |
| Call signatures                                                      |
|:---------------------------------------------------------------------|
| or( First alternative: [36m[3mMatchable[0m, Next alternative: [36m[3mMatchable[0m, ... ) |
| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | or() determines if lines match |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
