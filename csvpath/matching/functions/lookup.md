
# Lookup

Looks up values to find alternate values. The lookup uses a named path in CsvPaths.

    $employees[1*][ @lookedup = lookup("friends", #my_people, 0, 1) ]

This path says that we lookup the value of the #my_header column in the named path `my_people`. The values we lookup against are in the set of matched lines found by the `friends` named path. The comparison value is in the first column. The replacement value is in the second column.

A named path creates a list of matched rows held in memory. The named path also has a named CsvPath instance that offers variables, header names, etc.

After you are done with the path that uses `lookup()` you can drop the named path's collection of matched rows.

## Examples

Setup the CsvPaths instance and get a CsvPath. The example will use the food CSV file.

    nfiles = {"addresses": PATH, "numbers": NUMBERS, "food": FOOD}
    npaths = {"lookup_table": f"""${LOOKUP}[*][yes()] """}
    paths = CsvPaths(named_files=nfiles, named_paths=npaths)
    path = paths.csvpath()

Then parse the csvpath and collect the matching rows in the usual way:

    thepath = """$food[1*][
        @t = lookup("lookup_table", #1, 0, 1)
        print("The food category is $.variables.t")
    ]"""
    path.parse(thepath)
    lines = path.collect()

1 The `thepath` csvpath uses a `food` file
1 It does a `lookup()` using the `lookup_table` named path in the CsvPaths
1 That path, `lookup_table`, used the filename in the LOOKUP variable to do a scan and match of all rows in the lookup file
1 Those rows where column `#1` in the `food` file matched the first column in `lookup_table` resulted in the `@t` variable being set to the replacement value in column two of `lookup_table`


