Tally
tally() tracks the value of a variable, function, or header.

It always matches, effectively giving it nocontrib. Tally collects its
counts regardless of other matches or failures to match, unless you
add the onmatch qualifier.

Tally keeps its count in variables named for the values it is
tracking. It can track multiple values. Each of the values becomes a
variable under its own name. A header would be tracked under its name,
prefixed by tally_, as:

{'tally_firstname': {'Fred':3}}

Tally also tracks the concatenation of the multiple values under the
key tally. To use another key name add a non-keyword qualifier to
tally. For example, tally.birds(#bird_color, #bird_name) has a tally
variable of birds with values like blue|bluebird,red|redbird.
| Data signatures                   |
|:----------------------------------|
| tally( Value to count: [36m[3mAny[0m, ... ) |
| Call signatures                                        |
|:-------------------------------------------------------|
| tally( Value to count: [36m[3mHeader[0m|[36m[3mVariable[0m|[36m[3mFunction[0m, ... ) |
| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | tally() is a side-effect |
| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | [36m[3monmatch[0m             |
| Value qualifiers | [36m[3monmatch[0m             |
| Name qualifier   | [36m[3moptionally expected[0m |
