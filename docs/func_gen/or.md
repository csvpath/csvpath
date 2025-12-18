
## or()

or() implements OR logic in a csvpath writer-directed way.

Evaluation of or() completes before any errors are handled to allow
for the OR operation to be informed by branch invalidity.

Remember that logic-mode allows you to apply OR logic to the whole
csvpath, if that is needed. or() is of course more specific and
composable.

| Data signatures                                                                                                                                    |
|:---------------------------------------------------------------------------------------------------------------------------------------------------|
| or( First alternative: $${\color{green}None}$$ ǁ $${\color{green}Any}$$, Next alternative: $${\color{green}None}$$ ǁ $${\color{green}Any}$$, ... ) |

| Call signatures                                                      |
|:---------------------------------------------------------------------|
| or( First alternative: Matchable, Next alternative: Matchable, ... ) |

| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | or() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


