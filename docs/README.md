


- [The When Operator](#when)
- [Qualifiers](#qualifiers)
- [Error Handling](#errors)
- [More Examples](#examples)





## The print function

Before we get into the details of scanning and matching, let's look at what CsvPath can print. The `print` function has several important uses, including:

- Validating CSV and Excel files
- Debugging csvpaths
- Creating new CSV files based on an existing file

You can <a href='https://github.com/dk107dk/csvpath/blob/main/docs/printing.md'>read more about the mechanics of printing here</a>.

<a name="validating"></a>
### Validating CSV and Excel

CsvPath paths can be used for rules based validation. Rules based validation checks a file against content and structure rules but does not validate the file's structure against a schema. This validation approach is similar to XML's Schematron validation, where XPath rules are applied to XML.

There is no "standard" way to do CsvPath validation. The simplest way is to create csvpaths that print a validation message when a rule fails. For example:

```bash
    $test.csv[*][@failed = equals(#firstname, "Frog")
                 @failed.asbool -> print("Error: Check line $.csvpath.line_count for a row with the name Frog")]
```

Several rules can exist in the same csvpath for convenience and/or performance. Alternatively, you can run separate csvpaths for each rule. You can read more <a href='https://github.com/dk107dk/csvpath/blob/main/docs/paths.md'>about managing csvpaths here</a>.



<a name="when"></a>
## The when operator

`->`, the "when" operator, is used to act on a condition. `->` can take an equality, header, variable, or function on the left and trigger an assignment or function on the right. For e.g.

```bash
    [ last() -> print("this is the last line") ]
```

Prints `this is the last line` just before the scan ends.

```bash
    [ exists(#0) -> @firstname = #0 ]
```

Says to set the `firstname` variable to the value of the first column when the first column has a value. (Note that this could be achieved other simpler ways, including using the `notnone` qualifier on the variable.)

<a name="qualifiers"></a>
## Qualifiers

Qualifiers are tokens added to variable, header, and function names. They are separated from the names and each other with `.` characters. Each qualifier causes the qualified match component to behave in a different way than it otherwise would.

Qualifiers are quite powerful and deserve a close look. <a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>Read about qualifiers here.</a>

<a name="errors"></a>
## Error Handling

The CsvPath library handles errors according to policies set for the CsvPath and CsvPaths classes. Each class can have multiple approaches to errors configured together. The options are:
- Collect - an error collector collects errors for later inspection
- Raise - an exception is (re)raised that may halt the CsvPath process
- Stop - the CsvPath instance containing the offending problem is stopped; any others continue
- Fail - the CsvPath instance containing the offending problem is failed; processing continues
- Quiet - minimal error information is logged but otherwise handling is quiet

Raise and quiet are not useful together, but the others combine well. You can set the error policy in the config.ini that lives by default in the ./config directory.

Because of this nuanced approach to errors, the library will tend to raise data exceptions rather than handle them internally at the point of error. This is particularly true of matching, and especially the functions. When a function sees a problem, or fails to anticipate a problem, the exception is bubbled up to the top Expression within the list of Expressions held by the Matcher. From there it is routed to an error handler to be kept with other results of the run, or an exception is re-raised, or other actions are taken.


<a name="examples"></a>
## More Examples

There are more examples scattered throughout the documentation. Good places to look include:

- Here are a few <a href='https://github.com/dk107dk/csvpath/blob/main/docs/examples.md'>more real-looking examples</a>
- Try the Getting Started examples on <a href="https://www.csvpath.org">https://www.csvpath.org</a>
- The individual <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions.md'>function descriptions</a>
- The <a href='https://github.com/dk107dk/csvpath/tree/main/tests'>unit tests</a> and <a href='https://github.com/dk107dk/csvpath/tree/main/tests/grammar/match'>their match parts</a> are not realistic, but a good source of ideas.

To create example CsvPaths from your own data, try <a href='https://autogen.csvpath.org'>CsvPath AutoGen</a>. The huge caveat is that AutoGen uses AI so your results will not be perfect. You will need to adjust, polish, and test them.



