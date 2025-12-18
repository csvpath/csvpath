
## debug()

Sets the CsvPath Framework log level.

The level is set for the CsvPath class, not the CsvPaths class. That
means the log level is changed for particular csvpath currently
running, not any other csvpaths running after or along-side in a
breadth-first configuration.

| Data signatures                                 |
|:------------------------------------------------|
| debug( [info, debug, warn, error: None ǁ str] ) |

| Call signatures                                                                                                                                                                                                                                                                                  |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| debug( [info, debug, warn, error: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ Function ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header)] ) |

| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | debug() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


