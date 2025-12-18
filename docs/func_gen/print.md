
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

| Data signatures                                                         |
|:------------------------------------------------------------------------|
| print( print this: str|'', [print to specific Printer stream: str|''] ) |
| print( print this: str|'', [eval after: None|Any] )                     |

| Call signatures                                                     |
|:--------------------------------------------------------------------|
| print( print this: Term, [print to specific Printer stream: Term] ) |
| print( print this: Term, [eval after: Function|Equality] )          |

| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | print() is a side-effect |

| Context          | Qualifier               |
|:-----------------|:------------------------|
| Match qualifiers | onmatch, once, onchange |
| Value qualifiers | onmatch                 |


