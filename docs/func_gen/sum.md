
## sum()

Sum

Returns the running sum of a source.

sum() is similar to subtotal() but unlike subtotal it does not use
categorization to create multiple running totals.

Remember that CsvPath Language will convert None, bool, and the empty
string to int. This results in a predictable summation. If you are
looking for a way to make sure all lines have summable values try
using integer() or another approach.

| Data signatures              |
|:-----------------------------|
| sum( sum this: int ǁ float ) |

| Call signatures                                      |
|:-----------------------------------------------------|
| sum( sum this: Variable ǁ Function ǁ Term ǁ Header ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | sum() produces a calculated value |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |


