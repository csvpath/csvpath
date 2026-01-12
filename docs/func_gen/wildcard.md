
## wildcard()

A wildcard() schema type represents one or more headers that are otherwise unspecified.

It may take an int indicating the number of headers or a * to indicate any number of headers.

When wildcard() has no args it represents any number of headers, same as "*".

Note that wildcard() can represent 0 headers. Essentially, a wildcard by itself will not
            invalidate a document unless it defines a specific number of headers that are not found.

| Data signatures                                                                                                |
|:---------------------------------------------------------------------------------------------------------------|
| wildcard( , ... )                                                                                              |
| wildcard( $${\color{green}int}$$ ǁ $${\color{green}str}$$ ǁ $${\color{green}None}$$ ǁ $${\color{green}Any}$$ ) |

| Call signatures                                                                        |
|:---------------------------------------------------------------------------------------|
| wildcard( , ... )                                                                      |
| wildcard( [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |

| Purpose    | Value                                |
|:-----------|:-------------------------------------|
| Main focus | wildcard() determines if lines match |
| Type       | Wildcard is a line() schema type     |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
