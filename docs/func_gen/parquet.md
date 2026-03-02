
## parquet()

Generate Parquet files containing entities defined in the same way as
with line().

As a subclass of Line, the parquet() is a schema construction tool.
However, parquet() also has the function of outputing its valid
entities as .parquet files in the run dir. Lines that don't match will
not be written to the .parquet. You may define as many parquet()
entity as needed.

Using parquet() differs from line() in the following ways:

* parquet() must have an unique arbitrary name qualifier

* blank() are stored as BYTE_ARRAY

* blank() must have a name qualifier or a header name

* header indexes may only be used if the type has a name qualifier

* wildcard() are simply ignored

A parquet() might look like:

parquet.person( string.firstname(#0), string.lastname(#1) )

This will create a file called person.parquet in the result's run dir.
In the case of a one-off run using CsvPath, rather than CsvPaths, the
.parquet file will be created in the working directory.

Note that if you use CsvPath.next() or CsvPaths.next_paths() or
CsvPaths.next_by_line() you are responsible for calling flush() at the
end of the run in order to make sure all matched lines are flushed to
the .parquet file. When using CsvPaths next() methods use the
csvpath_instances property to flush each CsvPath in turn.

| Data signatures                                                                                       |
|:------------------------------------------------------------------------------------------------------|
| parquet( [function representing a data type: $${\color{green}None}$$ ǁ $${\color{green}Any}$$], ... ) |

| Call signatures                                                                                                                 |
|:--------------------------------------------------------------------------------------------------------------------------------|
| parquet( [function representing a data type: Wildcard ǁ String ǁ Boolean ǁ Decimal ǁ Date ǁ Nonef ǁ Blank ǁ Email ǁ Url], ... ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | parquet() determines if lines match |

| Context          | Qualifier                                                                                                                                                                |
|:-----------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [distinct](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#distinct) |
| Name qualifier   | optionally expected                                                                                                                                                      |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
