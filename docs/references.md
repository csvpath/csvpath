
# References

References give you a way to point within one csvpath to the results of another. The goal is to give you a way to make a transient relationship between csvpaths during an automated process.

A reference can point a variable or a header. Variables must be present at the end of the run. Any header is accessible by name or index. When a stand-alone reference points to a header it is an existence test asking the question, were there any values under this header in the whole file? A function using a header reference may handle values another way.

References are similar to the pointers you use in the `print()` function. They look like this:

```bash
    $[1][
        ~ this variable takes the value of a variable named "my_variable"
          in the most recent csvpaths run against the file identified
          as my_namedfile. ~
        @ref_one = $my_namedfile.variables.my_variable

        ~ this second variable takes its value from the "Today" key of the
          variable named "my_other_variable" ~
        @ref_two_with_tracking = $namedfile.variables.my_other_variable.Today

        print("The value of the first reference is $.variables.ref_one")
    ]
```

References point to the results of a path run against a file. They always refer to the most recent such run.



