Jinja
jinja() enables you to create a document using a template and tokens
derrived from the presently executing run and any number of past
csvpath results.

The jinja() context includes the same reference types as are available
in print() statements: variables, headers, metadata, and csvpath
runtime data. The present csvpath's information is under the key
"local", with those four dictionaries below that. Any past csvpath
results are aggregated in dicts keyed by the four reference types
names.

Be aware, Jinja is quite slow; much more so than print() which is
already taxing for high print volumes and/or very large files.
| Data signatures                                           |
|:----------------------------------------------------------|
| jinja( template: [36m[3mstr[0m, out: [36m[3mstr[0m, [results ref: [36m[3mstr[0m], ... ) |
| Call signatures                                                                                                                                                       |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| jinja( template: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, out: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, [results ref: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m], ... ) |
| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | jinja() is a side-effect |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
