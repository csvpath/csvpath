Regex
Matches a regular expression to a string.

The regular expression can be in argument one or two.

Optionally, the third argument returns a group from the match, if any
groups were defined.
| Data signatures                                                             |
|:----------------------------------------------------------------------------|
| regex( all headers: , regex: [36m[3mstr[0m )                                          |
| regex( str or regex: [36m[3mstr[0m|[36m[3m''[0m|[36m[3mNone[0m, str or regex: [36m[3mstr[0m|[36m[3m''[0m|[36m[3mNone[0m, [group: [36m[3mint[0m] ) |
| Call signatures                                                                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| regex( all headers: [36m[3mHeaders[0m, regex: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m )                                                                                           |
| regex( str or regex: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, str or regex: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, [group: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m] ) |
| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | regex() determines if lines match |
| Context          | Qualifier       |
|:-----------------|:----------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3masbool[0m |
| Value qualifiers | [36m[3monmatch[0m         |
