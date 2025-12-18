
## wildcard()

Wildcard

A wildcard() schema type represents one or more headers that are otherwise unspecified.

It may take an int indicating the number of headers or a * to indicate any number of headers.

When wildcard() has no args it represents any nuber of headers, same as "*".

Note that wildcard() can represent 0 headers. Essentially, a wildcard by itself will not
            invalidate a document unless it defines a specific number of headers that are not found.

| Data signatures                    |
|:-----------------------------------|
| wildcard( , ... )                  |
| wildcard( int ǁ str ǁ None ǁ Any ) |

| Call signatures   |
|:------------------|
| wildcard( , ... ) |
| wildcard( Term )  |

| Purpose    | Value                                |
|:-----------|:-------------------------------------|
| Main focus | wildcard() determines if lines match |
| Type       | Wildcard is a line() schema type     |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


