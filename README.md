
# <a href='https://www.csvpath.org/'><img src='https://www.csvpath.org/~gitbook/image?url=https%3A%2F%2F3739708663-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Forganizations%252FMXTJeGvaEsqwNG39F37h%252Fsites%252Fsite_SPBqJ%252Ficon%252FMCSxo7k6rXWnqoPE204u%252Fcsvpath-icon.png%3Falt%3Dmedia%26token%3D28869fdd-d54e-400e-8917-b8097f935f42&width=32&dpr=2&quality=100&sign=71ca9f3e&sv=1'/></a> About CsvPath

CsvPath defines a declarative syntax for inspecting and validating CSV and Excel files, and other tabular data.

CsvPath's goal is to make it easy to setup a Collect, Store, Validate-pattern flat-file landing zone that:
- Analyzes the content and structure of flat files
- Validates that files match expectations
- Reports on content validity
- Creates new derived files using copy-on-write

And does it all in an automation-friendly way.

CsvPath's validation is inspired by:
- XPath for XML files
- The ISO standard <a href='https://schematron.com/'>Schematron validation</a>

CsvPath is intended to fit with other DataOps and data quality tools. Files are streamed. The interface is simple. Metadata is plentiful. New functions are easy to create.

Read more about CsvPath and see realistic CSV and Excel validation examples at <a href='https://www.csvpath.org'>https://www.csvpath.org</a>.

If you need help, use the <a href='https://www.csvpath.org/getting-started/get-help'>contact form</a> or the <a href='https://github.com/csvpath/csvpath/issues'>issue tracker</a> or talk to one of our [sponsors](#sponsors).

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/csvpath?logoColor=green&color=green) ![GitHub commit activity](https://img.shields.io/github/commit-activity/m/dk107dk/csvpath) ![PyPI - Version](https://img.shields.io/pypi/v/csvpath)


# Contents

- [Motivation](#motivation)
- [Install](#install)
- [High-level Description](#description)
- [Running CsvPath](#running)
   - [Validation](#validating)
   - [Creating new files](#newfiles)
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
- [Grammar](#grammar)
- [Sponsors](#sponsors)

<a name="motivation"></a>
# Motivation

CSV files are everywhere!

A surprisingly large number of companies depend on CSV processing for significant amounts of revenue. Research organizations are awash in CSV. And everyone's favorite issue tracker, database GUI, spreadsheet, APM platform, and most any other type of tool we use day to day uses CSV for sharing. CSV is the lowest of common dominators. Many CSVs are invalid or broken in some way. Often times a lot of manual effort goes into finding problems and fixing them.

CsvPath is first and foremost a validation language. It describes tabular data in simple declarative rules that define what valid means for that data. CsvPath can also extract data, create reports, and do other useful things.

CsvPath's goal is to make simple validations almost trivial and more complex situations more manageable. It is a library, not a system, so it relies on being easy to integrate with other DataOps tools.


<a name="install"></a>
# Install

<a href='https://pypi.org/project/csvpath/'>CsvPath is available on PyPi</a>. Install with
```
    pip install csvpath
```

CsvPath has two optional dependencies:

- <a target='_blank' href='https://pypi.org/project/pandas/'>Pandas</a>
- <a target='_blank' href='https://pypi.org/project/smart-open/'>Smart-open</a>

Pandas data frames can be used as a data source, much like Excel or CSV files. Install CsvPath with the Pandas option:
```
    pip install csvpath[pandas]
```

Smart-open is an option for loading data files directly from S3. Install the Smart Open extra with:
```
    pip install csvpath[smart-open]
```

Both of these optional dependencies can make it harder to use CsvPath in certain specific use cases. For e.g., using Pandas in an AWS Lambda layer may be less straightforward. If you need the capabilities, they are easy to install, but if you don't CsvPath is lighter weight without.


# Description
<a name="description"></a>

CsvPath paths have three parts:
- a "root" file name
- a scanning part
- a matching part

The root of a csvpath starts with `$`. The match and scan parts are enclosed by brackets. Newlines are ignored.

A very simple csvpath might look like this:

```bash
    $filename[*][yes()]
```

This csvpath says open the file named `filename`, scan all the lines, and match every line scanned.

A slightly more functional csvpath could look like this:

```bash
    $people.csv[*][
        @two_names = count(not(#middle_name))
        last() -> print("There are $.variables.two_names people with only two names")]
```

This csvpath reads `people.csv`, counting the people without a middle name and printing the result after the last row is read.

A csvpath doesn't have to point to a specific file. As shown above, it can point to a specific file or it can instead use a logical name associated with a physical file or have no specific file indicator.

```bash
    $[*][
        @two_names = count(not(#middle_name))
        last() -> print("There are $.variables.two_names people with only two names")]
```

This version of the example has its file chosen at runtime.

See [more examples in this documentation](#examples). There are also <a href='https://www.csvpath.org'>lots more examples on csvpath.org</a>.

There is no limit to the amount of functionality you can include in a single csvpath. However, different functions run with their own performance characteristics. You should plan to test both the performance and functionality of your paths.

CsvPath was conceived as a data testing and extraction tool. Running it in production typically involves testing the paths in advance and automating the runs. There is a simple <a href='https://github.com/csvpath/csvpath/cli'>command line interface</a> that you can use to create and test csvpaths. You can <a href='https://www.csvpath.org/getting-started/your-first-validation-the-lazy-way'>read more about the CLI here</a>.

<a name="running"></a>
## Running CsvPath

CsvPath is <a href='https://pypi.org/project/csvpath/'>available on Pypi here</a>. The <a href='https://github.com/csvpath/csvpath'>git repo is here</a>.

Two classes provide the functionality: CsvPath and CsvPaths. Each has only a few external methods.

### CsvPath
(<a href='https://github.com/csvpath/csvpath/blob/main/csvpath/csvpath.py'>code</a>)
The CsvPath class is the basic entry point for running csvpaths.
|method                      |function                                                         |
|----------------------------|-----------------------------------------------------------------|
| next()                     | iterates over matched rows returning each matched row as a list |
| fast_forward()             | iterates over the file collecting variables and side effects    |
| advance()                  | skips forward n rows from within a `for row in path.next()` loop|
| collect()                  | processes n rows and collects the lines that matched as lists   |

### CsvPaths
(<a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/csvpaths.py'>code</a>)
The CsvPaths class helps you manage validations of multiple files and/or multiple csvpaths. It coordinates the work of multiple CsvPath instances.
|method                  |function                                                         |
|------------------------|-----------------------------------------------------------------|
| csvpath()              | gets a CsvPath object that knows all the file names available   |
| collect_paths()        | Same as CsvPath.collect() but for all paths sequentially        |
| fast_forward_paths()   | Same as CsvPath.fast_forward() but for all paths sequentially   |
| next_paths()           | Same as CsvPath.next() but for all paths sequentially           |
| collect_by_line()      | Same as CsvPath.collect() but for all paths breadth first       |
| fast_forward_by_line() | Same as CsvPath.fast_forward() but for all paths breadth first  |
| next_by_line()         | Same as CsvPath.next() but for all paths breadth first          |

To be clear, the purpose of `CsvPaths` is to apply multiple csvpaths per CSV file. Its breadth-first versions of the `collect()`, `fast_forward()`, and `next()` methods attempt to match each csvpath to each row of a CSV file before continuing to the next row. As you can imagine, for very large files this approach can be a big win.

There are several ways to set up CSV file references. Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/files.md'>more about managing CSV files</a>.

You also have important options for managing csvpaths. Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/paths.md'>about named csvpaths here</a>.

The simplest way to get started is using the CLI. <a href='https://www.csvpath.org/getting-started/your-first-validation-the-lazy-way'>Read about getting started with the CLI here</a>.

When you're ready to think about automation, you'll want to start with a simple driver. This is a very basic programmatic use of CsvPath.

```python
    path = CsvPath()
    path.parse("""
            $test.csv[5-25][
                #firstname == "Frog"
                @lastname.onmatch = "Bat"
                count() == 2
            ]
    """)

    for i, line in enumerate( path.next() ):
        print(f"{i}: {line}")
    print(f"The varibles collected are: {path.variables}")
```

The csvpath says:
- Open test.csv
- Scan lines 5 through 25
- Match the second time we see a line where the first header equals `Frog` and set the variable called  `lastname` to "Bat"

Another path that does the same thing a bit more simply might look like:

```bash
    $test[5-25][
        #firstname == "Frog"
        @lastname.onmatch = "Bat"
        count()==2 -> print( "$.csvpath.match_count: $.csvpath.line")
    ]
```

In this case, we're using the "when" operator, `->`, to determine when to print.

For lots more ideas see the unit tests and [more examples here](#examples).

There are a small number of configuration options. Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/config.md'>more about those here</a>.

## The print function

Before we get into the details of scanning and matching, let's look at what CsvPath can print. The `print` function has several important uses, including:

- Validating CSV files
- Debugging csvpaths
- Creating new CSV files based on an existing file

You can <a href='https://github.com/dk107dk/csvpath/blob/main/docs/printing.md'>read more about the mechanics of printing here</a>.

<a name="validating"></a>
### Validating CSV

CsvPath paths can be used for rules based validation. Rules based validation checks a file against content and structure rules but does not validate the file's structure against a schema. This validation approach is similar to XML's Schematron validation, where XPath rules are applied to XML.

There is no "standard" way to do CsvPath validation. The simplest way is to create csvpaths that print a validation message when a rule fails. For example:

```bash
    $test.csv[*][@failed = equals(#firstname, "Frog")
                 @failed.asbool -> print("Error: Check line $.csvpath.line_count for a row with the name Frog")]
```

Several rules can exist in the same csvpath for convenience and/or performance. Alternatively, you can run separate csvpaths for each rule. You can read more <a href='https://github.com/dk107dk/csvpath/blob/main/docs/paths.md'>about managing csvpaths here</a>.

<a name="newfiles"></a>
### Creating new CSV files

Csvpaths can also use the `print` function to generate new file content on system out. Redirecting the output to a file is an easy way to create a new CSV file based on an existing file. For e.g.

```bash
    $test.csv[*][ line_count()==0 -> print("lastname, firstname, say")
                  above(line_count(), 0) -> print("$.headers.lastname, $.headers.firstname, $.headers.say")]
```

This csvpath reorders the headers of the test file at `tests/test_resources/test.csv`. The output file will have a header row.

<a name="top-comments"></a>
# Comments
CsvPaths have file scanning instructions, match components, and comments. Comments exist at the top level, outside the CsvPath's brackets, as well as in the matching part of the path. Comments within the match part are covered below.

As well as documentation, comments outside the csvpath can:
- Contribute to a collection of metadata fields associated with a csvpath
- Switch on/off certain validation settings
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










