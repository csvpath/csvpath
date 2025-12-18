File fingerprint

Enters the SHA256 hash of the current data file into metadata.

A file's hash is available in run metadata. However, this function can
do a couple of things that may have value.

First, it can enter the data into the meta.json file as a stand-alone
value under any name you like.

Second and more importantly, it takes a fingerprint of a source-
mode:preceding run's data file. This allows you to easily confirm that
the input to the current csvpath was the exact output of the preceding
csvpath and different from the original data file.

| Data signatures    |
|:-------------------|
| file_fingerprint() |
| Call signatures    |
|:-------------------|
| file_fingerprint() |
|:------|:------------------------------------|
| Focus | file_fingerprint() is a side-effect |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |
... store_line_fingerprint
Store line fingerprint

Migrates a by-line fingerprint from its variable into run metadata. If
a name qualifier was used to create the by-line fingerprint the same
name must be used with this function.

| Data signatures          |
|:-------------------------|
| store_line_fingerprint() |
| Call signatures          |
|:-------------------------|
| store_line_fingerprint() |
|:------|:------------------------------------------|
| Focus | store_line_fingerprint() is a side-effect |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |
... count_bytes
Count bytes

Returns the total data bytes written count.

This function is only for named-path group runs. Individual CsvPath
instances do not write out data, so this value would be 0 for them.

|:------|:------------------------------------------|
| Focus | count_bytes() produces a calculated value |
|:-----------------|:--------|
| Match qualifiers | onmatch |
| Value qualifiers | onmatch |
... counter
Increments a variable. The increment is 1 by default.

Counters must be named using a name qualifier. Without that, the ID
generated for your counter will be tough to use.

A name qualifier is an arbitrary name added with a dot after the
function name and before the parentheses. It looks like
counter.my_name()

| Data signatures                          |
|:-----------------------------------------|
| counter( [amount to increment by: int] ) |
| Call signatures                                                                       |
|:--------------------------------------------------------------------------------------|
| counter( [amount to increment by: Term|Function|Header|Variable|Reference|Equality] ) |
|:------|:--------------------------------------|
| Focus | counter() produces a calculated value |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |
... xpath
Xpath

Finds the value of an XPath expression given a match component
containing XML.

| Data signatures                                             |
|:------------------------------------------------------------|
| xpath( from this XML: str|''|None, select this XPath: str ) |
| Call signatures                                                                                                             |
|:----------------------------------------------------------------------------------------------------------------------------|
| xpath( from this XML: Term|Variable|Header|Function|Reference, select this XPath: Term|Variable|Header|Function|Reference ) |
|:------|:------------------------------------|
| Focus | xpath() produces a calculated value |
|:-----------------|:--------|
| Match qualifiers | onmatch |
| Value qualifiers | onmatch |
