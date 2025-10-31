
# <a href='https://www.csvpath.org/'><img src='https://github.com/csvpath/csvpath/blob/main/docs/images/logo-wordmark-4.svg'/></a>

## Make Data File Feed Ingestion Higher Quality, Lower Risk, and More Agile

#### CsvPath Framework closes the gap between Managed File Transfer and the data lake, applications, analytics, and AI with a purpose-built, open source data file feeds preboarding solution.

These pages focus on *CsvPath Validation Language*. For more documentation on the whole data preboarding architecture, along with code, examples, and best practices, check out [csvpath.org](https://www.csvpath.org). For the FlightPath frontend application and API server head over to [flightpathdata.com](https://www.flightpathdata.com/flightpath.html).

CSV and Excel validation is at the core of the Framework. The Language defines a simple, declarative syntax for inspecting and validating files and other tabular data. Its mission is to end manual data checking and upgrading. The cost of manual processes and firefighting CSV and Excel problems can be as high as 50% of a DataOps and BizOps team's time. CsvPath Framework's automation-first approach helps scale back that unproductive and frustrating investment.

CsvPath Validation Language is inspired by:
- XPath and ISO standard <a href='https://schematron.com/'>Schematron validation</a>
- SQL schemas
- And business rules engines like Jess or Drools

If you need help getting started, there are lots of ways to reach us.
- Use the <a href='https://www.csvpath.org/getting-started/get-help'>contact form</a>
- The <a href='https://github.com/csvpath/csvpath/issues'>issue tracker</a>
- Email support@csvpath.org
- Or reach out to one of our [sponsors, below](#sponsors).

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/csvpath?logoColor=green&color=green) ![GitHub commit activity](https://img.shields.io/github/commit-activity/m/dk107dk/csvpath) ![PyPI - Version](https://img.shields.io/pypi/v/csvpath)


# Contents

- [Motivation](#motivation)
- [Install](#install)
- [Validation Approach](#approach)
- [Writing Validation Statements](#validating)
- [Running CsvPath](#running)
- [Grammars](#grammar)
- [Sponsors](#sponsors)

<a name="motivation"></a>

# Motivation

CSV and Excel files are everywhere! They are critical to successful data partnerships. They are a great example of how garbage-in-garbage-out threatens applications, analytics, and AI. And they are often the most unloved part of the data estate.

We rely on CSV because it the lowest common dominator. The majority of systems that have import/export capabilities accept CSV. But many CSV files are invalid or broken in some way due to partners having different priorities, SDLCs, levels of technical capability, and interpretations of requirements. The result is that untrustworthy data flows into the enterprise. Often times a lot of manual effort goes into tracing data back to problems and fixing them.

CsvPath Validation Language adds trust to data file feeds. It is a quality management shift-left that solves problems early where they are easiest to fix.

The Language is simple, function-oriented, and solely focused on validation of delimited data. It supports both schema definitions and rules-based validation. CsvPath Validation Language is declarative, for more concise and understandable data definitions. CsvPath can also extract and upgrade data, and create simple reports. Overall the goal is to automate human judgement and add transparency.

<a name="install"></a>

# Install

<a href='https://pypi.org/project/csvpath/'>CsvPath Framework is available on PyPi</a>. It has been tested on 3.10, 3.11 and 3.13.

The project uses Poetry and works fine with Uv. You can also install it with:
```
    pip install csvpath
```

CsvPath has an optional dependency on Pandas. Pandas data frames can be used as a data source, much like Excel or CSV files. To install CsvPath with the Pandas option do:
```
    pip install csvpath[pandas]
```

Pandas and its dependencies can make it harder to use CsvPath in certain specific MFT use cases. For e.g., using Pandas in an AWS Lambda layer may be less straightforward.


<a name="approach"></a>

<p></p>

# Validation Approach

CsvPath Validation Language is for creating "paths" that validate data streamed from files. A csvpath statement matches lines. A match does not mean that a line is inherently valid or invalid. That determination depends on how the csvpath statement was written.

For example, a csvpath statement can return all invalid lines as matches. Alternatively, it can return all valid lines as matches. It could also return no matching lines, but instead trigger side-effects, like print statements or variable changes.

## Structure
<a name="description"></a>
A csvpath statement has three structural parts:
- A root that may include a file name
- The scanning part, that declares what lines will be validated
- The matching part, that declares what lines will match

The root of a csvpath starts with `$`. The match and scan parts are enclosed by brackets. Newlines are ignored.


## Simple Examples
A trivial csvpath looks like this:

```bash
    $filename[*][yes()]
```

This csvpath says:
- Open the file: `filename`
- Scan all the lines: `*`
- And match every line scanned: `yes()`

In this case, a matching line is considered valid. Treating matches as valid is a simple approach. There are <a href='https://www.csvpath.org/topics/validation' target='_blank'>several possible validation strategies</a>.

Here is a more functional csvpath:

```bash
    $people.csv[*][
        @two_names = count(not(#middle_name))
        last() -> print("There are $.variables.two_names people with only two names")]
```

It scans the lines in `people.csv`, counts lines without a middle name, and prints the count when the last row is read.

A csvpath doesn't have to point to a specific file. It can instead simply have the scanning instruction come right after the root '$' like this:

```bash
    $[*][
        @two_names = count(not(#middle_name))
        last() -> print("There are $.variables.two_names people with only two names")]
```

In this case, the Framework chooses the csvpath's file at runtime.

<a name="validating"></a>

<p></p>

# Writing Validation Statements

At a high level, the functionality of a CsvPath Validation Language statement comes from:
* [Scanning instructions](https://github.com/csvpath/csvpath/blob/main/docs/scanning.md) - determine which lines the csvpath considers
* [Match components](https://github.com/csvpath/csvpath/blob/main/docs/matching.md) - determine which lines are matched and/or trigger side-effects
* [Comments](https://github.com/csvpath/csvpath/blob/main/docs/comments.md)

Each of these parts of a statement make significant functional contributions. This includes comments, which can have csvpath-by-csvpath configuration settings, integration hooks, and user-defined metadata.

<a name="running"></a>

# Running CsvPath

CsvPath is <a href='https://pypi.org/project/csvpath/'>available on Pypi here</a>. The <a href='https://github.com/csvpath/csvpath'>git repo is here</a>.

Two classes provide csvpath statement evaluation functionality: `CsvPath` and `CsvPaths`.

## CsvPath
(<a href='https://github.com/csvpath/csvpath/blob/main/csvpath/csvpath.py'>code</a>)
`CsvPath` is the most basic entry point for running csvpaths statements.
|method                      |function                                                         |
|----------------------------|-----------------------------------------------------------------|
| next()                     | iterates over matched rows returning each matched row as a list |
| fast_forward()             | iterates over the file collecting variables and side effects    |
| advance()                  | skips forward n rows from within a `for row in path.next()` loop|
| collect()                  | processes n rows and collects the lines that matched as lists   |

## CsvPaths
(<a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/csvpaths.py'>code</a>)
`CsvPaths` manages validations of multiple files and/or multiple csvpaths. It coordinates the work of multiple `CsvPath` instances.
|method                  |function                                                         |
|------------------------|-----------------------------------------------------------------|
| csvpath()              | gets a CsvPath object that knows all the file names available   |
| collect_paths()        | Same as CsvPath.collect() but for all paths sequentially        |
| fast_forward_paths()   | Same as CsvPath.fast_forward() but for all paths sequentially   |
| next_paths()           | Same as CsvPath.next() but for all paths sequentially           |
| collect_by_line()      | Same as CsvPath.collect() but for all paths breadth first       |
| fast_forward_by_line() | Same as CsvPath.fast_forward() but for all paths breadth first  |
| next_by_line()         | Same as CsvPath.next() but for all paths breadth first          |

The purpose of `CsvPaths` is to apply multiple csvpaths per CSV file and handle multiple files in sequence. `CsvPaths` has both serial and breadth-first versions of `CsvPath`'s `collect()`, `fast_forward()`, and `next()` methods. The breadth-first versions evaluate each csvpath for every line of a CSV file before restarting the evaluations with the next line.

## Simple Example
To learn about automation, start with a simple driver. This is a basic programmatic use of CsvPath. It checks a file against a trivial schema, iterating the matching lines.

```python
    path = CsvPath().parse("""
            $test.csv[1-25][
                line(
                    string.notnone(#firstname),
                    string.notnone(#lastname)
                )
            ]
    """)
    for i, line in enumerate( path.next() ):
        print(f"{i}: {line}")
```

For production operations consider using [FlightPath Server](https://www.flightpathdata.com/server.html), instead of coding your own driver scripts.

CsvPath is primarily for data automation, not interactive use. There is a simple <a href='https://github.com/csvpath/csvpath/cli'>command line interface</a> for quick dev iterations. <a href='https://www.csvpath.org/getting-started/your-first-validation-the-lazy-way'>Read more about the CLI here</a>. For more dev and ops functionality, use [FlightPath Data](https://www.flightpathdata.com/flightpath.html), the open source frontend to CsvPath Framework.

<a name="grammar"></a>

# Grammars

CsvPath Validation Language is built up from three grammars:
* The csvpath statement grammar - the main language
* A `print()` function grammar - a simple print capability with variable and reference substitution
* The Reference Language grammar - the file location and querying language used in validation and preboarding operations

Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/grammar.md'>more about the CsvPath grammar definition here</a>.


<a name="more-info"></a>

# More Info

For more information about preboarding and the whole of CsvPath Framework, visit <a href="https://www.csvpath.org">https://www.csvpath.org</a>.

For the development and operations frontend to CsvPath Framework, take a look at <a href='https://www.flightpathdata.com/flightpath.html'>FlightPath Data</a>.

And to learn about the backend API server, head over to <a href='https://www.flightpathdata.com/server.html'>FlightPath Server</a>.

<a name="sponsors"></a>

# Sponsors

<a href='https://www.atestaanalytics.com/' >
<img width="25%" src="https://raw.githubusercontent.com/dk107dk/csvpath/main/docs/images/logo-wordmark-white-on-black-trimmed-padded.png" alt="Atesta Analytics"/></a>
    <a href='https://www.datakitchen.io/'>
<img src="https://datakitchen.io/wp-content/uploads/2020/10/logo.svg"
style='width:160px; position:relative;bottom:-5px;left:15px' alt="DataKitchen" id="logo" data-height-percentage="45"></a>










