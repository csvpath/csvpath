Line
line() creates structural schema definitions.
Each line() function represents an entire line of the data file.

Using wildcards and blanks allows a line() to specify just certain
headers, rather than explicitly defining header-by-header. This also
allows for more line() functions to specify other structures within
the same data. You could, for e.g., define a person line() and an
address line() that lives side by side in the same rows.

Note that wildcard() and wildcard("*") are functionally the same.
| Data signatures                                            |
|:-----------------------------------------------------------|
| line( [function representing a data type: [36m[3mNone[0m|[36m[3mAny[0m], ... ) |
| Call signatures                                                                                              |
|:-------------------------------------------------------------------------------------------------------------|
| line( [function representing a data type: [36m[3mWildcard[0m|[36m[3mString[0m|[36m[3mBoolean[0m|[36m[3mDecimal[0m|[36m[3mDate[0m|[36m[3mNonef[0m|[36m[3mBlank[0m|[36m[3mEmail[0m|[36m[3mUrl[0m], ... ) |
| Purpose    | Value                            |
|:-----------|:---------------------------------|
| Main focus | line() determines if lines match |
| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3mdistinct[0m   |
| Name qualifier   | [36m[3moptionally expected[0m |
