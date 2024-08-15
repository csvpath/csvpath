
# Named Csvpaths

A csvpath has:
- A file identifier
- Scanning instructions, and
- Matching criteria

The match part in particular can get large. There is no limit on how many match components a csvpath can have. It is easy to come up with many validation rules, apply them to large files and have problems managing both the rules and the running time.

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

## Examples

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

A named path can reference a named file. To extend our example:

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
    paths.files_manager.set_named_files(nf)
    paths.paths_manager.set_named_paths(np)

    path = paths.csvpath()
    path.parse_named_path("monthly-costs")
    path.fast_forward()
```






