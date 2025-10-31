
<a name="identity"></a>
# A Csvpath's Identity

Every csvpath may have an optional identity string. The `identity` property is set in an outer comment using an ID or name field. The valid values of ID or name are all caps, initial caps, or all lower. For example:

```bash
    ~ ID: first_experiment ~
```

```bash
    ~ Id: second_experiment ~
```

```bash
    ~ name: my third experiment ~
```

If each of these has its own cvspath, the paths would be programmatically identified in Python like this:

```python
    path1.identity == "first_experiment"
```

```python
    path2.identity == "second_experiment"
```

```python
    path3.identity == "my third experiment"
```

The identity field is used in only a few places, at this time. You may see it when making a reference between csvpaths. See the reference docs for details.

You may also see `CsvPath.identity` (or a placeholder) used in argument validation error messages. This is a crucial usage. If you use `CsvPaths` instances to manage sets of csvpaths your arg validation messages can be hard to trace to the source unless you have an ID. When you add a name or id to your csvpaths' comments it will clearly point to where your problem is. Keep in mind that argument validation is not only a structure check when your csvpath is parsed, it is also a data check. Line by line, the fit of your data to your functions, or lack of fit, can tell you a lot about the validity of your file.

The identity property can also be used to pull results from `CsvPath`'s `ResultsManager` instance. For that, you would use the `get_specific_named_result` method. This is potentially important because the results manager manages sets of csvpaths by name, but the results of each csvpath in the set is distinct to that csvpath run performed by a single-use `CsvPath` instance.




