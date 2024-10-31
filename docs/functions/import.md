
# Import

`import()` gives you a way to inject one csvpath's matching rules into another. This can help with clarity, consistency, and testing.

Import parses both csvpaths, validates both, then puts the two together with the imported csvpath running just before where the import function was placed. Once the second csvpath has been imported it is as if you had written all the match components in the same place.

`import()` only works in the context of a CsvPaths instance. CsvPaths manages finding the imported csvpath. You make the import using a named-paths name, optionally with a specific csvpath identity within the named-paths group.

Named-paths names point to a set of csvpaths. You can point to the csvpath you want to import in two ways:
- Using a reference in the form $named-paths-name.csvpaths.csvpath-identity
- Giving a named-path name, optionally with a `#` and the identity of a specific csvpath

If you plan to import, remember to give your csvpaths an identity in the comments using the `id` or `name` metadata keys.

You can import csvpaths from the same named-paths group. That means you could even put all your csvpaths in one file and have them import each other as needed. When you do this you will still be running the whole named-paths group as a unit. Because of that, the csvpaths you import could be run twice. You can prevent that by setting the `run-mode` of the imported csvpaths to `no-run`.

## Examples

Let's set up the Python to run a simple import test:

```python
    cs = CsvPaths()
    cs.file_manager.add_named_files_from_dir("./csvs")
    cs.paths_manager.add_named_paths_from_dir("./csvpaths")
    cs.fast_forward_by_line(filename="food", pathsname="import")
    vars = cs.results_manager.get_variables("import")
    assert vars["import"] is True
```

The `import` csvpath looks like:

```bash
    $[1][
        print("I'm importing!")
        import("importable")
    ]
```

And the `importable` csvpath, also found in the `./csvpaths` directory, looks like:

```bash
    $[1][
        print("Import worked!")
        @import = yes()
    ]
```

Let's illustrate the all-in-one approach, including run-mode settings.

```bash
    ---- CSVPATH ----
    ~
        id: reset_headers
        run-mode: no-run
        description: each block of accounts is separated by one or more
                     blank lines. headers repeat for each block. it is
                     possible the headers change.
    ~
    $[*][ after_blank() -> reset_headers(skip()) ]

    ---- CSVPATH ----
    ~
        id: check account numbers
        description: a valid line starts with a header we're not checking.
                     then it has a 7-15 length whole number account ID.
                     the rest of the line doesn't matter for this rule.
    ~
    import( $statements.csvpaths.reset_headers )
    $[*][
        line(
            blank(),
            integer.notnone("account", 15, 7),
            wildcard()
        )
    ]

    ---- CSVPATH ----
    ~
        id: account open date
        description: all accounts in this file would be opened before
                     this year.
    ~
    import( $statements.csvpaths.reset_headers )

    $[*][ lt( date(#opened_on, "%Y"), thisyear() )  ]

```

These csvpaths declare two rules for lists of bank accounts. They are in one `.csvpath` file that is registered with the `CsvPaths`'s `PathManager` under one named-paths name: `statements`. We give each of them an ID for the purposes of identification between them, and also for better documentation and error tracing. And we set the `reset_headers` csvpath to not run on its own by setting the run mode `no-run`.

In this way we can keep the rules as concise as possible and focused on the validity of the data, not the quirks of this use case's CSV format.



