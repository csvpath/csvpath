
## stop_all()

Halts the containing csvpath's run abruptly and, in a named-paths
group run, prevents subsequent csvpaths from running.

stop_all() shuts down a whole named-paths group run in every run
method except collect_dynamic(). In a breadth-first run
(collect_by_line(), fast_forward_by_line() and next_by_line()) the
other csvpaths stop on the current line. In a serial run
(collect_paths(), fast_forward_paths() and next_paths()) the csvpaths
after this one do not run.

See stop() for more behavior details.

| Data signatures                                                           |
|:--------------------------------------------------------------------------|
| stop_all( [eval this: $${\color{green}None}$$ ǁ $${\color{green}Any}$$] ) |

| Call signatures                                                                                                        |
|:-----------------------------------------------------------------------------------------------------------------------|
| stop_all( [eval this: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ Equality] ) |

| Purpose                | Value                       |
|:-----------------------|:----------------------------|
| Main focus             | stop_all() is a side-effect |
| Has internal variables | False                       |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
