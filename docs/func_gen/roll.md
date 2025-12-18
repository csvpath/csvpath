
Roll

Rolls a date or datetime forward or backwards by a number of units.

The units accepted are: seconds, minutes, hours, days, months, years.
Both singular and plural forms are accepted.

| Data signatures                                            |
|:-----------------------------------------------------------|
| roll( date: Noneǁdateǁdatetime, how_many: int, unit: str ) |

| Call signatures                                                                                                 |
|:----------------------------------------------------------------------------------------------------------------|
| roll( date: FunctionǁHeaderǁVariableǁReference, how_many: FunctionǁHeaderǁVariableǁReferenceǁTerm, unit: Term ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | roll() produces a calculated value |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


