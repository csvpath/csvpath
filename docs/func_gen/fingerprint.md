
Fingerprint

Returns the fingerprint of a line or subset of a line's header values,
if headers are provided as arguments. The fingerprint is a SHA256 hash
of the values. A fingerprint can be used to lookup the line numbers of
dups found by has_dups(), count_dups(), and dup_lines().

Note that {self.name} gives the fingerprint solely from one line. By
contrast, line_fingerprint() progressively updates a hash value line-
by-line.

| Data signatures                              |
|:---------------------------------------------|
| fingerprint( [include this: None|Any], ... ) |

| Call signatures                            |
|:-------------------------------------------|
| fingerprint( [include this: Header], ... ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | fingerprint() produces a calculated value |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |


