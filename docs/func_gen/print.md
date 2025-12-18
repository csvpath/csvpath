
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
| print( print this: [36m[3mstr[0m|[36m[3m''[0m, [print to specific Printer stream: [36m[3mstr[0m|[36m[3m''[0m] ) |
| print( print this: [36m[3mstr[0m|[36m[3m''[0m, [eval after: [36m[3mNone[0m|[36m[3mAny[0m] )                     |

| Call signatures                                                     |
|:--------------------------------------------------------------------|
| print( print this: [36m[3mTerm[0m, [print to specific Printer stream: [36m[3mTerm[0m] ) |
| print( print this: [36m[3mTerm[0m, [eval after: [36m[3mFunction[0m|[36m[3mEquality[0m] )          |

| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | print() is a side-effect |

| Context          | Qualifier               |
|:-----------------|:------------------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3monce[0m, [36m[3monchange[0m |
| Value qualifiers | [36m[3monmatch[0m                 |


