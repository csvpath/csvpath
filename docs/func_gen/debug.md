Debug
Sets the CsvPath Framework log level.

The level is set for the CsvPath class, not the CsvPaths class. That
means the log level is changed for particular csvpath currently
running, not any other csvpaths running after or along-side in a
breadth-first configuration.
| Data signatures                               |
|:----------------------------------------------|
| debug( [info, debug, warn, error: [36m[3mNone[0m|[36m[3mstr[0m] ) |
| Call signatures                                                    |
|:-------------------------------------------------------------------|
| debug( [info, debug, warn, error: [36m[3mTerm[0m|[36m[3mFunction[0m|[36m[3mVariable[0m|[36m[3mHeader[0m] ) |
| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | debug() is a side-effect |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
