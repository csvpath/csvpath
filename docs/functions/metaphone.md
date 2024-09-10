
# Metaphone

`metaphone()` uses the Metaphone algorithm to generate a "sound-alike" phonetic transformation of a string. The algorithm is intended for English.

When given one argument the return is the Metaphone transformation.

When given two arguments the function attempts a lookup. The second argument must be a reference. The following requirements for references and this function are in effect:
- There must be a CsvPaths instance parent to the currently running CsvPath instance
- The lookup must be to a named-path
- A single csvpath under the named-path key is preferred because the first named-result is used
- The reference must be to a variable with tracking values; i.e. a dictionary

Our lookup needs access to a Dict[str, str]. The dictionary holds lookup keys to canonical values. The most obvious way to create the lookup dictionary is with the `track()` function. This lookup pattern works great for `metaphone()`. It is also applicable elsewhere.

## Examples

A simple use that would result in an identical Metaphone translation for the words "Sacks" and "Sax" looks like this:

```bash
    $[*][ @meta = metaphone(#name) ]
```

To set up a canonicalization match component takes a bit more effort, but not too much. First you need your lookup table.

```python
    paths = CsvPaths()
    paths.files_manager.add_named_file(
        name="lookups", path="tests/test_resources/named_files/lookup_names.csv"
    )
    paths.paths_manager.add_named_paths_from_file(
        name="meta",
        file_path="tests/test_resources/named_paths/metaphone_lookup.csvpaths",
    )
    paths.fast_forward_paths(pathsname="meta", filename="lookups")
```

This Python fragment loads our lookup table using this .csv:

```
names
Zach
Sax
I.B.M
add
Smithson
```

And this csvpath:

```bash
$[1*][
    track.canonical( metaphone(#names), #names )
]
```

Now that our lookup is ready we can do this in Python and/or csvpath:

```python
    path = paths.csvpath()
    path.parse(f"""
          $some_path_doesnt_matter_for_this_example.csv[*][
            @sac1 = metaphone("Sacks", $meta.variables.canonical)
            @sac2 = metaphone("Sax", $meta.variables.canonical)
            @same = equals(@sac1, @sac2)
    ]"""
    path.fast_forward()
    assert path.variables["same"] is True
```





