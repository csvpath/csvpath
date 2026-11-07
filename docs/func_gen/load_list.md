
## load_list()

Load list

Loads a list of values, one per line, from a text file. The value is a
list (a tuple, which cannot be changed) that in() and other functions
can use, e.g.:

@ids.tmp = load_list("ids") in( #id, @ids )

In a named-paths group run the argument is the list's name, and the
list is the group's assets/<name>.txt. Lists are stored with the paths
manager's asset manager store_list(). Outside a group run the argument
is the path of a .txt file.

Blank lines are skipped and each value is stripped of surrounding
whitespace. The list is loaded once, when the csvpath is validated; a
list that cannot be loaded is an error then, before any line is read.
Use the tmp qualifier to keep a large list out of vars.json.

| Data signatures                                        |
|:-------------------------------------------------------|
| load_list( list name or path: $${\color{green}str}$$ ) |

| Call signatures                                                                                            |
|:-----------------------------------------------------------------------------------------------------------|
| load_list( list name or path: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |

| Purpose                | Value                                   |
|:-----------------------|:----------------------------------------|
| Main focus             | load_list() produces a calculated value |
| Has internal variables | False                                   |

| Context          | Qualifier                                                                                                                                                                                                                                                                                                                  |
|:-----------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                                                                                                         |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
