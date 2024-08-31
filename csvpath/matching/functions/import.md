
# Import

`import()` gives you a way to inject one csvpath's matching rules into another. This can help with clarity, consistency, and testing.

Import parses both csvpaths, validates both, then puts the two together with the imported csvpath running just before where the import function was placed.

Once the second csvpath has been imported it ceases to have its own independent existance. It is as if you had written all the match components in the same place.

`import()` only works in the context of a CsvPaths instance. CsvPaths manages finding the imported csvpath. You make the import using a named-paths name.

Named-paths names point to a set of csvpaths. When you use import you are always referencing the first path in the set. For this reason, when using imports, you should put each importable csvpath under its own named-paths name. If you are using a directory as your source of named paths, this means having just one csvpath in any files that will be used as imports.

## Examples

Let's set up the Python to run the simplest import test:

```python
    cs = CsvPaths()
    cs.files_manager.add_named_files_from_dir("./csvs")
    cs.paths_manager.add_named_paths_from_dir("./csvpaths")
    cs.fast_forward_by_line(filename="food", pathsname="import")
    vars = cs.results_manager.get_variables("import")
    assert vars["import"] is True
```

The `import` csvpath looks like:

```bash
    $[*][
        print("Attempting import!")
        import("importable")
    ]
```

And the `importable` csvpath, also found in the `./csvpaths` directory, looks like:

```bash
    $[*][
        print("Import worked!")
        @import = yes()
    ]
```




