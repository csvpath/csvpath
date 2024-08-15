
# Named Files

The file identifier following the root `$` and preceding the scanning part of the csvpath can be:
- A relative or absolute file path
- A logical identifier that points indirectly to a physical file, as described below
- The empty string, in which case the file association happens in CsvPaths on the fly

Filenames must match this regular expression `[A-Z,a-z,0-9\._/\-\\#&]+`. I.e. they have:

- alphanums
- forward and backward slashes
- dots
- hash marks
- dashes
- underscores, and
- ampersands.

## Using CsvPaths To Work With Files

You can use the `CsvPaths` class to set up a list of named files so that you can have more concise csvpaths. Named files can take the form of:

- A JSON file with a dictionary of file system paths under name keys
- A dict object passed into the CsvPaths object containing the same name-to-file-path structure
- A file system path pointing to a directory that will be used to populate the named files with all contained files

Using named files requires `CsvPaths`, but the configuration happens in a CsvPaths's <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/managers/files_manager.py'>FilesManager</a>.

## Example

```python
    paths = CsvPaths()
    paths.files_manager.add_named_file("test", "tests/test_resources/test.csv")
    path = paths.csvpath()
    path.parse( """$test[*][#firstname=="Fred"]""" )
    rows = path.collect()
```
This csvpath will be applied to the file named `"test"` and match rows where the `firstname` is `"Fred"`. The matched rows will be returned from the `collect()` method.

## FilesManager

The FilesManager methods are:

| Method                              | Description                                                         |
|-------------------------------------|---------------------------------------------------------------------|
| add_named_files_from_dir(dir_path)  | Adds all files to the named files set by names minus any extension  |
| add_named_files_from_json(filename) | Adds named files paths from a dict JSON structure found in the file |
| set_named_files(Dict[str, str])     | Replaces all named files with the contents of a dict                |
| add_named_file(name, path)          | Adds a single named file path                                       |
| get_named_file(name)                | Gets the full file path associated with the name                    |
| remove_named_file(name)             | Removes a named file                                                |


Using these methods you can setup a CsvPaths, like the example above, then use a csvpath like `$logical_name[*][yes()]` to apply the csvpath to the file named `logical_name` in your CsvPaths object's `files_manager`. This use is easy and nearly transparent.

