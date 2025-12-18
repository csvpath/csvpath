
Collect
When collect() is used only values for the indicated headers are
returned during the run. If there are four columns in a data file and
two are collected each line returned by CsvPath.next() will contain
two values.

| Data signatures                            |
|:-------------------------------------------|
| collect( header identifier: [36m[3mint[0m|[36m[3mstr[0m, ... ) |
| collect( header: [36m[3mAny[0m, ... )                |

| Call signatures                         |
|:----------------------------------------|
| collect( header identifier: [36m[3mTerm[0m, ... ) |
| collect( header: [36m[3mHeader[0m, ... )          |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | collect() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


