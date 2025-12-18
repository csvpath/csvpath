Sum
Returns the running sum of a source.

sum() is similar to subtotal() but unlike subtotal it does not use
categorization to create multiple running totals.

Remember that CsvPath Language will convert None, bool, and the empty
string to int. This results in a predictable summation. If you are
looking for a way to make sure all lines have summable values try
using integer() or another approach.
| Data signatures            |
|:---------------------------|
| sum( sum this: [36m[3mint[0m|[36m[3mfloat[0m ) |
| Call signatures                                |
|:-----------------------------------------------|
| sum( sum this: [36m[3mVariable[0m|[36m[3mFunction[0m|[36m[3mTerm[0m|[36m[3mHeader[0m ) |
| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | sum() produces a calculated value |
| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | [36m[3monmatch[0m             |
| Value qualifiers | [36m[3monmatch[0m             |
| Name qualifier   | [36m[3moptionally expected[0m |
