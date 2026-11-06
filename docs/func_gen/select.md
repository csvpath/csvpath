
## select()

Selects from a table column into a stack variable.

A where clause can be provided as an argument. The where clause cannot
be complex, for example, involving other tables or views.

The where clause uses CsvPath Language Variable syntax. Use @var to
reference the csvpath's var variable. For example, to select values in
the ID column according to a group name you might do:

select.my_ids("ID", "mytable", "where group='@group'", yes())

Here "ID" is the column name to select from, "mytable" is the table,
and the where clause limits the returned values by checking the
"group" column against the @group variable.

select() functions may take an arbitrary name qualifier to create a
variable without an explicit assignment. If a name is provided, the
select will only run if the variable does not exist. Put another way,
to cache a select(), simply give it a name, like:
select.my_cached_select(). The my_cached_select variable will be
populated once. If you need to refresh it, use clear().



| Data signatures                                                                                                                                                                                                               |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| select( column name: $${\color{green}Any}$$ ǁ '' ǁ $${\color{green}None}$$, table name: $${\color{green}str}$$, where clause: $${\color{green}None}$$ ǁ $${\color{green}str}$$ ǁ '', connect string: $${\color{green}str}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| select( column name: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), table name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function), where clause: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function), connect string: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ) |

| Purpose    | Value                                |
|:-----------|:-------------------------------------|
| Main focus | select() produces a calculated value |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
