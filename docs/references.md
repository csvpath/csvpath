
# References

References give you a way to point from within one csvpath to the results of another. The goal is to give you a way to make a transient relationship between csvpaths during an automated process.

A reference can point a variable or a header. Variables must be present at the end of the run. Any header is accessible by name or index. When a stand-alone reference points to a header it is an existence test asking the question, _were there any values under this header in the whole file?_ A function that uses a header reference may handle referenced values another way.

References are similar to the pointers you use in the `print()` function. They look like this:

```bash
    $[1][
        ~ this variable takes the value of a variable named "my_variable"
          in the most recent csvpaths run against the file identified
          as "my_namedfile". ~
        @ref_one = $my_namedfile.variables.my_variable

        ~ this second variable takes its value from the "Today" key of the
          variable named "my_other_variable" ~
        @ref_two_with_tracking = $namedfile.variables.my_other_variable.Today

        print("The value of the first reference is $.variables.ref_one")
    ]
```

References point to the results of a csvpath run against a file. They always refer to the most recent such run.

A reference is composed of the following parts in this order:
- A named-path reference
- The word `variables` or `headers`
- A variable or header name
- Optionally a tracking value name

For e.g.:

```bash
    $orders.variables.total
```

This reference points to the `total` variable resulting from the most recent CsvPath run using the csvpath(s) identified to CsvPaths by the name "orders". To do that, we might set it up like this:

```python
        cs = CsvPaths()
        cs.files_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="orders", pathsname="shipping-validations")
        #
        # now use the $orders.variables.total by reference in another csvpath
        #
        path = cs.csvpath()
        path.parse("$[*][
            @monthly = $shipping-validations.variables.total lt(@monthly, 1000) -> fail_and_stop() ]")
        path.fast_forward()
```

This path doesn't do much, other than illustrate the use of references. It says that if the value found by the most recent run of the `orders` CSV file was too low we declare it invalid and stop processing.

A note of warning. As you can see, CsvPath and CsvPaths are working together to make this reference possible. References only have meaning in the context of a CsvPaths instance. The intention is for references to fail gracefully when there is no CsvPaths instance orchestrating CsvPath instances. However, you should definitely not count on graceful or predictable failure. Instead, just be mindful how you are using your paths and write them accordingly.

In the same vein, your csvpath could collect a different number of headers than the original file has, potentially causing problems with references. If you use `collect()` to capture, say, 2 headers out of 5, your indexes would be different and the resulting lines would have only two values, not five. Moreover, you would be missing 3 header names. Since references by name are converted to indexes your references might use the correct name of a captured column but under the hood attempt to access it using the wrong index. Today there is no work around for this, other than just not doing it.




