
# Fail, Failed, and Valid

CsvPath's most important use is rules-based validation of CSV files. There are three main ways of performing validation:

- Printing a message when a rule fails giving a location and reason
- Collecting failed rows
- Programmatically checking the state of a failure signal

The `fail()` function enables the third of these.

When a validation rule identifies a problem you can use `fail()` to indicate that the CSV file is invalid. The reasoning or evidence, in the form of row values, is typically needed as well. However, programmatically, a printout is hard to interpret. A list of rows' values is also difficult to interpret because valid rows can match as readily as invalid ones.

Setting the state of a csvpath is easy. In the csvpath just add `fail()` when there is a problem. Checking the state of the csvpath is also easy. You just check the CsvPath object's is_valid property.

Within your csvpath you can check if a CSV is invalid using `failed()` or `valid()`. For e.g.:

```bash
    $file[*][
        #firstname == 'Fox' -> fail()
        failed() -> stop()
    ]
```

Also, be aware that you can use `fail_and_stop()` to terminate a scan and declare the file invalid at the same time.

## Examples

For this csvpath that says that nobody in the CSV can have the name "Fox":

```bash
    $file[*][ #firstname == 'Fox' -> fail() ]
```

We can check our CsvPath to see if the file is valid:

```python
    path = csvpaths.csvpath()
    path.parse(namedpath)
    path.fast_forward()
    if path.is_valid:
        print("Woohoo, no foxes")
    else:
        print("Oh no, foxes!")
```

