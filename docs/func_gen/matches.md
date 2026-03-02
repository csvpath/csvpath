
## matches()

Matches if the rest of the line matches.

This function is useful in a few less common cases. For example, to
achieve a result like:

@x.increase.onchange = #0 -> push("top", @x)

due to the language's grammar you would actually need to do:

@x.increase.onchange = int(#1) matches() -> push("top", @x)

| Data signatures   |
|:------------------|
| matches()         |

| Call signatures   |
|:------------------|
| matches()         |

| Purpose    | Value                                                     |
|:-----------|:----------------------------------------------------------|
| Main focus | matches() produces a calculated value and decides matches |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
