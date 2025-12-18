
Metaphone

metaphone() uses the Metaphone algorithm to generate a "sound-alike"
phonetic transformation of a string. The algorithm is intended for
English.

When given one argument the return is the Metaphone transformation.

When given two arguments the function attempts a lookup. The second
argument must be a reference. There are four requirements for
references with metaphone():

- The currently running CsvPath instance must be part of a named-paths
group run

- The reference must be to a variable with tracking values. (E.g.
$mygroup.variables.cities).

The easiest way to create the lookup variable is often with the
track() function. You can also use put() or other functions. The
lookup data structure must be like a Python Dict[metaphone:str,
canonical:str].

At this time only simple references are available for identifying the
lookup data. That means that references get data from the most recent
run available and variables are found in the super set of all
variables generated in the results of the run.

| Data signatures                                       |
|:------------------------------------------------------|
| metaphone( transform this: str, [lookup data: dict] ) |

| Call signatures                                                                                        |
|:-------------------------------------------------------------------------------------------------------|
| metaphone( transform this: Term ǁ Function ǁ Header ǁ Variable ǁ Reference, [lookup data: Reference] ) |

| Purpose    | Value                                   |
|:-----------|:----------------------------------------|
| Main focus | metaphone() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


