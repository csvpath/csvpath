
## advance()

Skips processing N-lines ahead. The lines skipped will not be
considered or collected as matched or unmatched.

advance() is similar to skip(). skip() cuts-short the processing of
its line and jumps to the next line. advance() skips N-number of whole
lines after the line where it is evaluated.

| Data signatures                  |
|:---------------------------------|
| advance( lines to advance: int ) |

| Call signatures                                         |
|:--------------------------------------------------------|
| advance( lines to advance: Term ǁ Variable ǁ Function ) |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | advance() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


