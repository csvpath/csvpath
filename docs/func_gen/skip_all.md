
Skip all
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

| Data signatures                 |
|:--------------------------------|
| skip_all()                      |
| skip_all( eval this: [36m[3mNone[0m|[36m[3mAny[0m ) |

| Call signatures                          |
|:-----------------------------------------|
| skip_all()                               |
| skip_all( eval this: [36m[3mFunction[0m|[36m[3mEquality[0m ) |

| Purpose    | Value                       |
|:-----------|:----------------------------|
| Main focus | skip_all() is a side-effect |

| Context          | Qualifier     |
|:-----------------|:--------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3monce[0m |
| Value qualifiers | [36m[3monmatch[0m       |


