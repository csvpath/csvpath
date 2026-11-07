
## jsonschema()

Validates an JSON document using an JSONSchema.

The project must be configured such that JSON docs are acceptable data
files. Do this by setting the    [inputs] files value to a comma
separated string of extensions that includes "xml".

If the run is performed by a CsvPaths instance, the schema parameter
must be a file in the named-paths group and just the name of the file,
not the full path to the file.

If the run is performed programmatically by a CsvPath instance, there
is no named-paths group, so the file name parameter must be the full
path to the JSONSchema file.

If validation fails, the errors will be presented as CsvPath
Validation Language errors.

Validation using a JSONSchema implies that the data is a JSON
document, not a file of line-by-line tabular data. When the validation
engine sees the jsonschema() in your validation, it stops after one
data line because the validation of the document is complete.

Any of the validation run methods on CsvPaths work for JSONSchema.
(e.g. collect_paths). Because there is no enumerated data output from
the csvpath statement doing the validation, the run's stop property is
set (equivalent to calling the stop() function) after the one line
required for validation. That makes fast_forward_paths the most
obvious choice for run method.

Regardless of run method, multiple JSONSchemas can be applied simply
by adding the jsonschema() function to multiple csvpath statements in
the same named-paths group.

| Data signatures                                            |
|:-----------------------------------------------------------|
| jsonschema( JSONSchema file name: $${\color{green}str}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                          |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| jsonschema( JSONSchema file name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ) |

| Purpose                | Value                                  |
|:-----------------------|:---------------------------------------|
| Main focus             | jsonschema() determines if lines match |
| Has internal variables | False                                  |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
