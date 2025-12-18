
## print()

print() prints to one or more default or designated Printer instances.

Print can have a function or equality argument that is evaluated after
printing completes.

There are four reference data types available during printing:

- variables

- headers

- metadata

- csvpath

The latter is the runtime metrics and config for the presently running
csvpath. See csvpath.org, the CsvPath Framework GitHub repo docs, or
the Runtime Print Fields section of the FlightPath help tabs for more
details. The run_table() function also gives a good view of the
available fields.

| Data signatures                                                                                                   |
|:------------------------------------------------------------------------------------------------------------------|
| print( print this: $${\color{green}str}$$ ǁ '', [print to specific Printer stream: $${\color{green}str}$$ ǁ ''] ) |
| print( print this: $${\color{green}str}$$ ǁ '', [eval after: $${\color{green}None}$$ ǁ $${\color{green}Any}$$] )  |

| Call signatures                                                                                                                                                                                                 |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| print( print this: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), [print to specific Printer stream: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)] ) |
| print( print this: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), [eval after: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ Equality] )    |

| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | print() is a side-effect |

| Context          | Qualifier                                                                                                                                                                                                                                              |
|:-----------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [once](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#once), [onchange](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onchange) |
| Value qualifiers | onmatch                                                                                                                                                                                                                                                |


