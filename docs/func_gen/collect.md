
Collect

When collect() is used only values for the indicated headers are
returned during the run. If there are four columns in a data file and
two are collected each line returned by CsvPath.next() will contain
two values.

| Data signatures                            |
|:-------------------------------------------|
| collect( header identifier: intǁstr, ... ) |
| collect( header: Any, ... )                |

| Call signatures                         |
|:----------------------------------------|
| collect( header identifier: Term, ... ) |
| collect( header: Header, ... )          |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | collect() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


