
Line fingerprint
Sets the line-by-line SHA256 hash of the current data file into a
variable. You can use a name qualifier to name the variable.
Otherwise, the name will be by_line_fingerprint.

Since the hash is created line-by-line, progressively modifying a
hash, it changes on every line scanned.

Even if all lines are scanned, the fingerprint at the end of the run
is highly unlikely to match the file fingerprint from the
manifest.json. This difference is due to the way lines are fed into
the fingerprint algorithm, skipped blanks, and other artifacts. Line
fingerprint simply gives you an additional tool for ascertaining the
identity of certain input data bits.

| Data signatures    |
|:-------------------|
| line_fingerprint() |

| Call signatures    |
|:-------------------|
| line_fingerprint() |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | line_fingerprint() is a side-effect |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | [36m[3monmatch[0m             |
| Value qualifiers | [36m[3monmatch[0m             |
| Name qualifier   | [36m[3moptionally expected[0m |


