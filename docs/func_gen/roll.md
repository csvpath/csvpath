
## roll()

Rolls a date or datetime forward or backwards by a number of units.

The units accepted are: seconds, minutes, hours, days, months, years.
Both singular and plural forms are accepted.

| Data signatures                                                |
|:---------------------------------------------------------------|
| roll( date: None ǁ date ǁ datetime, how_many: int, unit: str ) |

| Call signatures                                                                                                               |
|:------------------------------------------------------------------------------------------------------------------------------|
| roll( date: Function ǁ Header ǁ Variable ǁ Reference, how_many: Function ǁ Header ǁ Variable ǁ Reference ǁ Term, unit: Term ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | roll() produces a calculated value |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


