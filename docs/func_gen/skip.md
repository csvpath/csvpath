
Skip
Jumps to the next line abruptly.

skip() short-circuits the full csvpath evaluation of a line. Earlier
match components will be evaluated; although, with the exception of
any components carrying the onmatch qualifier, which pushes them to
the back of the csvpath processing order.

Like stop(), skip() can optionally take a function argument that will
determine if skip() is triggered. In this way, skip() acts as if it
has an embedded when/do operator.

| Data signatures             |
|:----------------------------|
| skip()                      |
| skip( eval this: [36m[3mNone[0m|[36m[3mAny[0m ) |

| Call signatures                      |
|:-------------------------------------|
| skip()                               |
| skip( eval this: [36m[3mFunction[0m|[36m[3mEquality[0m ) |

| Purpose    | Value                   |
|:-----------|:------------------------|
| Main focus | skip() is a side-effect |

| Context          | Qualifier     |
|:-----------------|:--------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3monce[0m |
| Value qualifiers | [36m[3monmatch[0m       |


