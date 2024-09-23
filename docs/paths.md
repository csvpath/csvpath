
# Named Csvpaths

A csvpath has:
- A file identifier
- Scanning instructions, and
- Matching criteria

The match part in particular can get large. There is no limit on how many match components a csvpath can have. It is easy to come up with many validation rules, apply them to large files, and have problems managing both the rules and the running time.

In those cases it may be helpful to register paths with a `CsvPaths` object. Using paths by name is more than just convenient. The benefits include:

- The ability to break big csvpaths into smaller smaller ones in the same file or different files
- Grouping validation rules
- Running multiple paths "breadth-first" row-by-row
- Smaller names and easier file organization

## Using PathsManager

To use named csvpaths you must use a `CsvPaths` object. Your setup happens in CsvPath's `paths_manager`, a `PathsManager` object. PathsManager has the following methods:

| Method                                | Description                                                      |
|---------------------------------------|------------------------------------------------------------------|
| add_named_paths_from_dir(dir_path)    | Adds each file's csvpaths keyed by the filename minus extension  |
| set_named_paths_from_json(filename)   | Sets the named paths as a JSON dict of keys to lists of csvpaths |
| set_named_paths(Dict[str, List[str]]) | Sets the named paths as a Python dict of keyed lists of csvpaths |
| add_named_paths(name, path:List[str]) | Adds as list of csvpaths                                         |
| get_named_paths(name)                 | Gets the list of csvpaths keyed by the name                      |
| remove_named_paths(name)              | Removes a list of csvpaths

## Simple Examples

As a simple example, let's set up two csvpaths and use one of them by name.

```python
    np = {
        "monthly-exports":"""
            $exported_goods.csv[*][#origin=="usa" -> print("$.match_count local products")]""",
        "monthly-costs":"""
            $converted.csv[0][~check all columns arrived ~ @c=count_headers() print("$.variables.c")]"""
    }
    paths = CsvPaths()
    paths.paths_manager.set_named_paths(np)
    path = paths.csvpath()
    path.parse_named_path("monthly-costs")
    path.fast_forward()
```

A named path can reference a named file. To extend our example with named files:

```python
    nf = {
        "exports":"files/shipping/exports/exported_goods-2024-07.csv",
        "costs":"files/costs/july-costs.csv"
    }

    np = {
        "monthly-exports":"""$exports[*][#origin=="usa" -> print("$.match_count local products")]""",
        "monthly-costs":"""$costs[0][~check all columns arrived ~ @c=count_headers() print("$.variables.c")]"""
    }

    paths = CsvPaths()
    paths.file_manager.set_named_files(nf)
    paths.paths_manager.set_named_paths(np)

    path = paths.csvpath()
    path.parse_named_path("monthly-costs")
    path.fast_forward()
```

## Breadth First

There may be cases when you want to run a set of csvpaths one after another. This requires iterating the CSV file multiple times. `CsvPaths` makes it easy to run csvpaths in series, but that typically isn't necessary and the runtime performance may not be acceptable.

`CsvPaths` also makes it easy to run multiple csvpaths against a file breadth-first. That means CsvPaths will attempt to match every row in the file against all the provided csvpaths before it moves on to the next row.

As well as the performance implications, this approach let's you break up big validation rules into sets of small rules for easier management. This can be handled two ways:

- Add the named csvpaths programmatically or in a JSON file
- Put the named csvpaths in a single file with each path separated by `---- CSVPATH ----`

To do the latter, create the file then import it by adding its directory. The csvpaths will be separated and applied together by using their name; i.e. the file name minus the extension.

For example these two csvpaths are from the file at `tests/test_resources/named_paths/food.csvpaths`:

```bash
    $[*][
        ~ invalid if there is too much candy on the manifest ~

        #type == "candy" -> push( "candy", count_lines() )
        above(size("candy"), 1) -> print("$.count_lines: too much candy at: $.variables.candy ")
        above(size("candy"), 1) -> fail_and_stop()
    ]

    ---- CSVPATH ----

    $[1*][
        ~ call out any modern foods we see ~
        count_lines.nocontrib() == 1 -> print(" ")
        above(#year, 1850) -> print("$.count_lines. $.headers.food is modern food")
    ]
```

We can apply them breadth-first using this code:

```python
    cs = CsvPaths()
    cs.file_manager.set_named_files(FILES)
    cs.paths_manager.add_named_paths_from_dir(NAMED_PATHS_DIR)
    for line in cs.next_by_line(filename="food", pathsname="many"):
        valid = cs.results_manager.is_valid("many")
        if valid:
            print("Yup, still valid!")
```





