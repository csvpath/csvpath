
## line()

line() creates structural schema definitions.

Each line() function represents an entire line of the data file.

Using wildcards and blanks allows a line() to specify just certain
headers, rather than explicitly defining header-by-header. This also
allows for more line() functions to specify other structures within
the same data. You could, for e.g., define a person line() and an
address line() that lives side by side in the same rows.

Note that wildcard() and wildcard("*") are functionally the same.

| Data signatures                                              |
|:-------------------------------------------------------------|
| line( [function representing a data type: None ǁ Any], ... ) |

| Call signatures                                                                                                              |
|:-----------------------------------------------------------------------------------------------------------------------------|
| line( [function representing a data type: Wildcard ǁ String ǁ Boolean ǁ Decimal ǁ Date ǁ Nonef ǁ Blank ǁ Email ǁ Url], ... ) |

| Purpose    | Value                            |
|:-----------|:---------------------------------|
| Main focus | line() determines if lines match |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch, distinct   |
| Name qualifier   | optionally expected |


