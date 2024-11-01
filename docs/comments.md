
# Comments

Comments are delimited with tilde, the `~` character. They have several closely related functions in CsvPath:
- Providing documentation
- Creating referenceable metadata in well-known and/or ad hoc fields
- Shutting down ("commenting out") functionality that is not wanted at a certain moment, but which the cvspath author doesn't want to delete
- Switching on settings

All these functions are completely optional.

- [Inner and outer](#inner)
- [Metadata fields](#metadata)
- [Settings](#settings)
- [Identity](#identity)

<a name="inner"></a>
## Inner and outer

There are two types of comments:
- Outer comments that are before and/or after the cvspath
- Inner comments that sit between match components

Outer comments provide documentation, create metadata, and set settings. They do not comment out functionality.

Inner comments provide internal documentation and can comment-out match components. Comments cannot live within a match component. Remember that a when/do or assignment expression (sometimes referred to as an Equality) is a match component including both the left- and right-hand sides. A comment cannot be beside an `=`, `==`, or `->` operator.

<a name="metadata"></a>
## Metadata fields

Outer comments can create metadata fields that live in a `CsvPath` instance and are accessible within the csvpath using references. A field is set by putting a colon after a word. The word becomes the field and everything up to the next coloned word is the value of the field.

For example, to set author, description, and date fields you would do something like:

```bash
    ~ author: Anatila
      description: This is my example csvpath. date: 1/1/2022
    ~
```

As you can see, line breaks between fields are not needed. If you want to stop a metadata field but don't want to put another directly after it, add a stand-alone colon. For example:

```bash
    ~ When in the course of human events title: Declaration : DRAFT
    ~
```

In this example the `title` field equals `Declaration`. The word DRAFT is outside the metadata fields. However, the whole original comment is also captured as its own `original_comment` field. This need to capture a field separated from following comment content may also occur if you have comments above and below the csvpath.

You can use metadata field two ways:
- Programmatically by referencing your `CsvPath` instance's `metadata` property
- Within your csvpath's `print()` statements using print references in the form `$.metadata.title`

When you are using a `CsvPaths` instance to manage multiple `CsvPath` instances programmatic access to your CsvPath instances' metadata is through the results manager. For example:

```python
    results = csvpaths.results_manager.get_named_results("food")
    for r in results:
        print(f"metadata is here: {r.csvpath.metadata} or, alternatively, here: {r.metadata}")
```

<a name="settings"></a>
## Settings

Metadata fields can be used to control certain run modes:
- `logic-mode` -- sets the CsvPath instance to operate in AND or OR mode
- `return-mode` -- instructs the CsvPath instance to return matches or lines that did not match
- `print-mode` -- determines if the printouts from `print()` go to the terminal's standard out, or not
- `validation-mode` -- sets the validation reporting actions and channels
- `run-mode` -- indicates if a csvpath should be run by its CsvPath instance
- `explain-mode` -- if set, an explanation of the match results is dumped to INFO for each line processed

The values for each are:

- `logic-mode` == `OR` or `AND` (`AND` is the default)
- `return-mode` == `no-matches` or `matches` (`matches` is the default)
- `print-mode` == `no-default` or `default` (`default` is the default)
- `run-mode` == `no-run` or `run` (`run` is the default)
- `explain-mode` == `no-explain` or `explain` (`no-explain` is the default)
- `validation-mode` ==
    - `print` or `no-print` (`print` is on by default) and/or
    - `raise` or `no-raise` and/or
    - `log` (`log` can only be turned off programmatically)
    - `stop` or `no-stop`
    - `fail` or `no-fail`

The metadata settings happen after the `parse()` method and before `collect()`, `fast_forward()`, or `next()` processes the file. If neither the positive (e.g. `print`) or the negative (e.g. `no-print`) is found the fallback is the setting in config.ini.

Metadata driven settings are effective only for the csvpath they are declared in. When you are using a `CsvPaths` instance to manage a multi-`CsvPath` instance run these metadata fields give you a way to configure different behavior for each `CsvPath` in the run.

<a name="identity"></a>
## Identity

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




