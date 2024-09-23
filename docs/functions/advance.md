
# Advance

`advance()` allows your csvpath to skip ahead some number of rows. Skipping rows avoids the processing overhead of checking if the rows match. The rows skipped are, of course, iterated; however, depending on the content of your csvpath, substantial latency may be avoided. Advance may be most useful for sampling or spot-checking.

Note that you cannot advance during an advance. This is because `advance()` is a match component and will not be activated during the skipped iterations of an existing call to `advance()`.

## Examples

```bash
    $[1*][
        ~ collect a sample of 1000 responders ~
        below(count(), 1001) -> advance(random(1,50))
    ]
```

This csvpath collects a random sample of 1000 rows, starting after the header row. The sampled rows are from 1 to 50 lines apart.

One way to run it looks like this, using dict objects to identify the csvpaths and files. There are, of course, other simple ways to do it.

```python
    paths = CsvPaths()
    paths.file_manager.set_named_files(nf)
    paths.paths_manager.set_named_paths(np)
    lines = paths.collect_paths(pathsname="sample", filename="survey")
```

