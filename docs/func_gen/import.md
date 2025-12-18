Import
Imports one csvpath into another. The imported csvpath's match
components are copied into the importing csvpath. Scan instructions
are not imported.

Using import() can help with clarity, consistency, efficiency through
reuse, and testing.

Import parses both csvpaths, validates both, then puts the two
together with the imported csvpath running just before where the
import function was placed. Once the second csvpath has been imported
it is as if you had written all the match components in the same
place.

Keep in mind that in CsvPath Language, order matters. Import may come
at any point in a csvpath, allowing you to managed ordering. Remember
that the onmatch qualifier reorders match components so that those
with onmatch are evaluted after those without onmatch.

import() only works in the context of a CsvPaths instance. CsvPaths
manages finding the imported csvpath. You make the import using a
named-paths name, optionally with a specific csvpath identity within
the named-paths group.

Named-paths names point to a set of csvpaths. You can point to the
csvpath you want to import in two ways:

- Using a reference in the form $named-paths-name.csvpaths.csvpath-
identity

- Giving a named-path name, optionally with a # and the identity of a
specific csvpath

If you plan to import, remember to give your csvpaths an identity in
the comments using the id or name metadata keys.

You can import csvpaths from the same named-paths group. That means
you could even put all your csvpaths in one file and have them import
each other as needed. When you do this you will still be running the
whole named-paths group as a unit. Because of that, the csvpaths you
import could be run twice. You can prevent that by setting the run-
mode of the imported csvpaths to no-run.
| Data signatures            |
|:---------------------------|
| import( import this: [36m[3mstr[0m ) |
| Call signatures                       |
|:--------------------------------------|
| import( import this: [36m[3mTerm[0m|[36m[3mReference[0m ) |
| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | import() is a side-effect |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
