Advance
Skips processing N-lines ahead. The lines skipped will not be
considered or collected as matched or unmatched.

advance() is similar to skip(). skip() cuts-short the processing of
its line and jumps to the next line. advance() skips N-number of whole
lines after the line where it is evaluated.
| Data signatures                  |
|:---------------------------------|
| advance( lines to advance: [36m[3mint[0m ) |
| Call signatures                                     |
|:----------------------------------------------------|
| advance( lines to advance: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mFunction[0m ) |
| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | advance() is a side-effect |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
