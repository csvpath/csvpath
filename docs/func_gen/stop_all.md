
## stop_all()

Halts the containing csvpath's run abruptly and, in certain named-
paths group runs, prevents subsequent csvpaths from running.

stop_all() shuts down a whole named-paths group run when the run
method is either breadth-first or the iterative programmatic
next_paths() method. Breadth-first runs are triggered with the
collect_by_line(), fast_forward_by_line(), and next_by_line() methods.

See stop() for more behavior details.

| Data signatures                     |
|:------------------------------------|
| stop_all( [eval this: None ǁ Any] ) |

| Call signatures                                                                                                        |
|:-----------------------------------------------------------------------------------------------------------------------|
| stop_all( [eval this: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ Equality] ) |

| Purpose    | Value                       |
|:-----------|:----------------------------|
| Main focus | stop_all() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


