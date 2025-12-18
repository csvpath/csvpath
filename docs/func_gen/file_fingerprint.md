
## file_fingerprint()

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

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | file_fingerprint() is a side-effect |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |
| Name qualifier   | optionally expected                                                                |


