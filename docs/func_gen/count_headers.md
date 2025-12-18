
## count_headers()

count_headers() returns the number of headers currently in-effect. It
is our expected number, not the number of values we actually get.

Keep in mind that the number of headers in a file can change at any
time. Each time we call reset_headers() the return from
count_headers() is also reset.

| Purpose    | Value                                       |
|:-----------|:--------------------------------------------|
| Main focus | count_headers() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


