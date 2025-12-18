
## fail_all()

Indicates that all csvpaths that are running as a group should be marked failed. 

I.e., the data file triggering the failure will have failed across the board, even if only one csvpath caught a problem.

| Purpose    | Value                                |
|:-----------|:-------------------------------------|
| Main focus | fail_all() determines if lines match |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


