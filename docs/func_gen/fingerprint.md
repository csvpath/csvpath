
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
| fingerprint( [include this: [36m[3mNone[0m|[36m[3mAny[0m], ... ) |

| Call signatures                            |
|:-------------------------------------------|
| fingerprint( [include this: [36m[3mHeader[0m], ... ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | fingerprint() produces a calculated value |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | [36m[3monmatch[0m             |
| Value qualifiers | [36m[3monmatch[0m             |
| Name qualifier   | [36m[3moptionally expected[0m |


