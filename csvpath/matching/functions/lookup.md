
# Lookup

Looks up values to find alternate values. The lookup uses a named path in CsvPaths.

    $employees[1*][ @lookedup = lookup("friends", #my_people, 0, 1) ]

This path says that we lookup the value of the `#my_people` column. The values we lookup against are in the matched lines found by the `friends` named path. The comparison value is in the first column of `friends`. The replacement value is in the second column of `friends`.

A named path creates a list of matched rows held in memory. The named path also has a named CsvPath instance that offers variables, header names, etc.

After you are done with the path that uses `lookup()` you can drop the named path's collection of matched rows to reduce memory usage. If the lookup table is needed again it will be recreated.

## Examples

Setup the CsvPaths instance and get a CsvPath. The example will use the food CSV file.

First we identify our lookup table:

    LOOKUP = "tests/test_resources/lookup.csv"

Then we configure our CsvPaths instance:

    named_files = {"addresses": PATH, "numbers": NUMBERS, "food": FOOD}
    named_paths = {"lookup_table": f"""${LOOKUP}[*][yes()] """}
    paths = CsvPaths(named_files=named_files, named_paths=named_paths)
    path = paths.csvpath()

We then parse our csvpath and collect the matching rows in the usual way:

    mypath = """$food[1*][
        @t = lookup("lookup_table", #1, 0, 1)
        print("The food category is $.variables.t")
    ]"""
    path.parse(thepath)
    lines = path.collect()

1. The `mypath` csvpath uses a `food` named file from the CsvPaths
2. It does a `lookup()` using the `lookup_table` named path in the CsvPaths
3. That path, `lookup_table`, used the filename in the `LOOKUP` variable to do a scan and match of all rows in the lookup file
4. Those rows where column `#1` in the `food` file matched the first column in `lookup_table` resulted in the `@t` variable being set to the replacement value in column two of `lookup_table`


