
# Comments

Csvpath comments are delimited with tilde, the `~` character. They are positioned:
* Before the csvpath root, and/or
* Between top-level match components in the matching part

Comments have several closely related functions in CsvPath:
- [Presenting csvpath documentation](#inner)
- [Setting key-value user-defined metadata](#metadata)
- [Setting the ID of the csvpath](#identity)
- [Switching on/off settings, known as "modes"](#modes)
- [Providing configuration settings to integrations](#integrations)

All of these functions are completely optional.

<a name="inner"></a>
## Inner and Outer Comments

There are two types of comments:
- Outer comments that are before and/or, less commonly, after the csvpath
- Inner comments that sit between top-level match components

For example:
```
    ~ I am an outer comment ~
    $[*][ @a = "a" ~and I am an inner comment~ @b = "b" ]
```

Outer comments provide documentation, create metadata, and set settings. They do not comment out functionality, but they can comment out the entire csvpath. Inner comments provide more specific documentation and can comment-out match components.

Comments cannot live within a match component. Remember that a when/do or assignment expression (sometimes referred to as an Equality) is an Equality match component. The Equality component includes both the left- and right-hand sides. A comment cannot sit beside an `=`, `==`, or `->` operator. Neither can a comment be within a function.

<a name="metadata"></a>
## Metadata Fields

Outer comments can create metadata fields that live in a `CsvPath` instance. Metadata fields are accessible programmatically and within the csvpath using references. In addition, `CsvPaths` instance runs output a `metadata.json` file containing all metadata fields, among other values. There is more information on `metadata.json` on [csvpath.org](https://www.csvpath.org).

A metadata field is created by putting a colon after a word. The word becomes the field key. Everything up to the next colon-word key, or the end of the comment, is the value of the field. Newlines are ignored but are captured to the value of the field.

For example, this comment sets author, description, and date fields:

```bash
    ~ author: Anatila
      description: This is my example csvpath.
      date: 1/1/2022
    ~
```

To stop a metadata field without putting another directly after it, add a stand-alone colon. For example:

```bash
    ~ When in the course of human events title: Declaration : DRAFT ~
```

In this example:
* `When in the course of human events` is not part of a metadata field
* The `title` field equals `Declaration`
* The word `DRAFT` is also not part of a metadata field
* The whole original comment is also captured to an `original_comment` field

You can use metadata fields two ways:
- Programmatically by referencing your `CsvPath` instance's `metadata` property
- Within your csvpath's `print()` statements using print references in the form `$.metadata.title`
- Programmatically through a `CsvPaths` instance's `Result` object

In the latter case, access to metadata is through the `ResultsManager`. For example:

```python
    results = csvpaths.results_manager.get_named_results("food")
    for r in results:
        print(f"metadata is here: {r.csvpath.metadata} or, alternatively, here: {r.metadata}")
```

Programmatic access to results metadata is covered further on [csvpath.org](https://www.csvpath.org).

<a name="identity"></a>
## The Csvpath's Identity

Every csvpath has an identity that is used to refer to it programmatically and from within csvpaths. Identities are set using special metadata fields.

[Read more about csvpath identities here](https://github.com/csvpath/csvpath/blob/main/docs/comments/identity.md).


<a name="modes"></a>
## Mode Settings

Mode setting are special metadata fields that apply settings for the duration of a csvpath evaluation.

[Read more about the modes here](https://github.com/csvpath/csvpath/blob/main/docs/comments/modes.md).


<a name="integrations"></a>
## Integration Settings

CsvPath Framework comes integrated with many DataOps tools, including OpenLineage, Slack, SQL databases, OpenTelemetry, and more. Settings for these integrations is done by a combination of special metadata fields and `config.ini` file settings.

[Read more about integration settings here](https://github.com/csvpath/csvpath/blob/main/docs/comments/integrations.md).


