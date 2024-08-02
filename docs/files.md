
# Filenames and Named Files

The string following the `$` can be a relative or absolute file path. It could alternatively be a logical identifier that points indirectly to a physical file, as described below.

Filenames must match this regular expression `[A-Z,a-z,0-9\._/\-\\#&]+`. I.e. they have:

- alphanums
- forward and backward slashes
- dots
- hash marks
- dashes
- underscores, and
- ampersands.

As noted above, you can use the `CsvPaths` class to set up a list of named file paths so that you can have more concise csvpaths. Named paths can take the form of:

- A JSON file with a dictionary of file paths under name keys
- A dict object passed into the CsvPaths object containing the same named path structure
- The path to a csv file that will be put into the named paths dict under its name minus extension
- A file system path pointing to a directory that will be used to populate the named paths dict with all contined files

You can then use a csvpath like `$logical_name[*][yes()]` to apply the csvpath to the file named `logical_name` in the CsvPaths object's named paths dict. This use is nearly transparent:

    paths = CsvPaths(filename = "my_named_paths.json")
    path = paths.csvpath()
    path.parse( """$test[*][#firstname=="Fred"]""" )
    path.collect()

If my_named_paths.json contains the following structure, the name `test` will be used to find `tests/test_resources/test.csv`. The parse method will apply the csvpath and the collect method will gather all the matched rows.

    { "test":"test/test_resources/test.csv" }





