
## skip_all()

Jumps to the next line abruptly. In a named-paths group run, where the
run method is breadth-first, skip_all() jumps to the next line without
any following csvpaths seeing the line at all.

A breadth-first run method is one of collect_by_line(),
fast_forward_by_line, or next_by_line(). These methods pass each line
through all csvpaths in the named-paths group before continuing to the
next line.

skip_all() short-circuits the full csvpath evaluation of a line.
Earlier match components will be evaluated; although, with the
exception of any components carrying the onmatch qualifier, which
pushes them to the back of the csvpath processing order.

See skip() for more behavior details.

| Data signatures                                                         |
|:------------------------------------------------------------------------|
| skip_all()                                                              |
| skip_all( eval this: $${\color{green}None}$$ ǁ $${\color{green}Any}$$ ) |

| Call signatures                                                                                                      |
|:---------------------------------------------------------------------------------------------------------------------|
| skip_all()                                                                                                           |
| skip_all( eval this: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ Equality ) |

| Purpose    | Value                       |
|:-----------|:----------------------------|
| Main focus | skip_all() is a side-effect |

| Context          | Qualifier                                                                                                                                                        |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [once](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#once) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                               |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
