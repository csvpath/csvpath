
# Named Paths

A csvpath has a file identifier, a scan part, and a match part. The match part in particular can get large. In some cases it may be helpful to register paths with a `CsvPaths` object and then use them by name. For example:

```python

    named_paths = {
        "monthly-exports":"""$exported_goods.csv[*][#origin=="usa" -> print("$.match_count local products")]""",
        "monthly-costs":"""$converted.csv[0][~check all columns arrived ~ @c=count_headers() print("$.variables.c")]"""        }

    paths = CsvPaths(named_paths=named_paths)
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

    paths = CsvPaths(named_paths=np, named_files=nf)
    path = paths.csvpath()
    path.parse_named_path("monthly-costs")
    path.fast_forward()

```






