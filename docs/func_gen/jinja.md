
## jinja()

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
| jinja( template: str, out: str, [results ref: str], ... ) |

| Call signatures                                                                                                                                                                               |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| jinja( template: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, out: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, [results ref: Term ǁ Variable ǁ Header ǁ Function ǁ Reference], ... ) |

| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | jinja() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


