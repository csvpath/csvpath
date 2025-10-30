


- [Comments](#top-comments)
- [Scanning](#scanning)
- [Matching](#matching)
   - [Match Components](#components)
      - [Terms](#terms)
      - [Functions](#functions)
      - [Headers](#headers)
      - [Variables](#variables)
      - [Equalities](#equalities)
      - [References](#references)
   - [Comments Within Match](#comments)
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


<a name="top-comments"></a>
# Comments
CsvPaths have file scanning instructions, match components, and comments. Comments exist at the top level, outside the CsvPath's brackets, as well as in the matching part of the path. Comments within the match part are covered below.

As well as documentation, comments outside the csvpath can:
- Contribute to a collection of metadata fields associated with a csvpath
- Switch on/off certain validation and DataOps tool integration settings
- Set the identity of a csvpath within a group of csvpaths

A comment starts and ends with a `~` character. Within the comment, any word that has a colon after it is considered a metadata key. The metadata value is anything following the key up till a new metadata key word is seen or the comment ends.

For example, this comment says that the csvpath has the name `Order Validation`:

```bash
    ~ name: Order Validation
      developer: Abe Sheng
    ~
    $[*][ count(#order) == 10 ]
```

The name `Order Validation` is available in CsvPath's `metadata` property along with the developer's name. You can use any metadata keys you like. All the metadata is available during and after a run, giving you an easy way to name, describe, attribute, etc. your csvpaths.

You can <a href='https://github.com/dk107dk/csvpath/blob/main/docs/comments.md'>read more about comments and metadata here</a>.

<a name="scanning"></a>
# Scanning

The scanning part of a csvpath enumerates selected lines. For each line returned, the line number, the scanned line count, and the match count are available. The set of line numbers scanned is also available.

The scan part of the path starts with a dollar sign to indicate the root, meaning the file from the top. After the dollar sign comes the file path. The scanning instructions are in a bracket. The rules are:
- `[*]` means all
- `[3*]` means starting from line 3 and going to the end of the file
- `[3]` by itself means just line 3
- `[1-3]` means lines 1 through 3
- `[1+3]` means lines 1 and line 3
- `[1+3-8]` means line 1 and lines 3 through eight

<a name="matching"></a>
# Matching

The match part is also bracketed. Matches have space separated components or "values" that are ANDed together. The components' order is important. A match component is one of several types:

- Term
- Function
- Variable
- Header
- Equality
- Reference

<a name="Components"></a>
<a name="terms"></a>
## Term
A string, number, or regular expression value.

|Returns | Matches     | Examples        |
|--------|-------------|-----------------|
|A value | Always true | `"a value"`     |

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/terms.md'>Read about terms here</a>.

<a name="functions"></a>
## Function
A composable unit of functionality called once for every row scanned.

|Returns    | Matches    | Examples      |
|-----------|------------|---------------|
|Calculated | Calculated | `count()`     |

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions.md'>Read about functions here</a>.

<a name="variables"></a>
## Variable
A stored value that is set or retrieved once per row scanned.

|Returns | Matches | Examples      |
|--------|---------|---------------|
|A value | True when set. (Unless the `onchange` qualifier is used). Alone it is an existence test. | `@firstname` |

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/variables.md'>Read about variables here</a>.

<a name="headers"></a>
## Header
A named header or a header identified by 0-based index.
_(CsvPath avoids the word "column" for reasons we'll go into later in the docs)._

|Returns | Matches | Examples      |
|--------|---------|---------------|
|A value | Calculated. Used alone it is an existence test. | `#area_code` |

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/headers.md'>Read about headers here</a>.

<a name="equalities"></a>
## Equality
Two of the other types joined with an "=" or "==".

|Returns | Matches | Examples      |
|--------|---------|---------------|
|Calculated | True at assignment, otherwise calculated. | `#area_code == 617` |

<a name="references"></a>
## Reference
References are a way of pointing to data generated by other csvpaths. Referenced data is held by a CvsPaths instance. It is stored in its named-results. The name is the one that identified the paths that generated it.

References can point to:
- Variables
- Headers

The form of a reference is:

```bash
    $named_path.variables.firstname
```

This reference looks in the results named for its CSV file. The qualifier `variables` indicates the value is a variable named `firstname`.

|Returns    | Matches                                   | Examples               |
|-----------|-------------------------------------------|------------------------|
|Calculated | True at assignment, otherwise calculated. | `@q = $orders.variables.quarter` |


Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/references.md'>more about references here</a>.


<a name="comments"></a>
## Comments

You can comment out match components by wrapping them in `~`. Comments can be multi-line. At the moment the only limitations are:

- Comments cannot include the `~` (tilde) and `]` (right bracket) characters
- Comments cannot go within match components, only between them

Examples:

```bash
    [ count() ~this is a comment~ ]
```

```bash
    [    ~this csvpath is
          just for testing.
          use at own risk~
       any()
    ]
```

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

<a name="grammar"></a>
## Grammar

Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/grammar.md'>more about the CsvPath grammar definition here</a>.


<a name="more-info"></a>
# More Info

Visit <a href="https://www.csvpath.org">https://www.csvpath.org</a>

<a name="sponsors"></a>
# Sponsors

<a href='https://www.atestaanalytics.com/' >
<img width="25%" src="https://raw.githubusercontent.com/dk107dk/csvpath/main/docs/images/logo-wordmark-white-on-black-trimmed-padded.png" alt="Atesta Analytics"/></a>
    <a href='https://www.datakitchen.io/'>
<img src="https://datakitchen.io/wp-content/uploads/2020/10/logo.svg"
style='width:160px; position:relative;bottom:-5px;left:15px' alt="DataKitchen" id="logo" data-height-percentage="45"></a>










