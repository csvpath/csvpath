
# <a href='https://www.csvpath.org/'><img src='https://github.com/csvpath/csvpath/blob/main/docs/images/logo-wordmark-4.svg'/></a>

## CsvPath Framework Makes Data File Feed Ingestion Higher Quality, Lower Risk, and More Agile

#### Close the gap between Managed File Transfer and the data lake, applications, analytics, and AI with a purpose-built, open source data file feeds preboarding solution.

These pages focus on *CsvPath Validation Language*. For more documentation on the whole data preboarding architecture, along with code, examples, and best practices, check out https://www.csvpath.org. For the FlightPath frontend application and API server head over to [flightpathdata.com](https://www.flightpathdata.com/flightpath.html).

CSV and Excel validation is at the core of the Framework. The Language defines a simple, declarative syntax for inspecting and validating files and other tabular data. Its mission is to end manual data checking and upgrading. The cost of manual processes and firefighting to DataOps and BizOps teams can be as high as 50%. CsvPath Framework's automation-first approach can help scale back that unproductive and frustrating investment.

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
- [Python Interface](#pdocs)
- [Approach](#approach)
- [Structure](#structure)
- [Validating Files](#validating-files)
- [Running CsvPath](#running)
- [Grammar](#grammar)
- [Sponsors](#sponsors)

<a name="motivation"></a>
# Motivation

CSV and Excel files are everywhere! They are critical to successful data partnerships. They are a great example of how garbage-in-garbage-out threatens applications, analytics, and AI. And they are often the most unloved part of the data estate.

We rely on CSV because it the lowest common dominator. The majority of systems that have import/export capbilities accept CSV. But many CSV files are invalid or broken in some way due to partners having different priorities, SDLCs, levels of technical capability, and interpretations of requirements. The result is that untrustworthy data flows into the enterprise. Often times a lot of manual effort goes into tracing data back to problems and fixing them.

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


<a name="pdocs"></a>
# Python Interface
<a href='https://csvpath.github.io/csvpath/' target='_blank'>Python docs are here</a>.
CsvPath Framework's public interface is streamlined. For our focus on just CsvPath Validation Language, the `csvpath.CsvPath` and `csvpath.CsvPaths` classes are where most of the magic happens. For more comprehensive information on the whole Framework head over to [csvpath.org](https://www.csvpath.org).

# Approach
<a name="approach"></a>

CsvPath Validation Language is for creating "paths" that validate streams of tabular file data. A csvpath statement matches lines. A match does not mean that a line is inherently valid or invalid. That determination depends on how the csvpath statement was written.

For example, a csvpath statement can return all invalid lines as matches. Alternatively, it can return all valid lines as matches. It could also return no matching lines, but instead trigger side-effects, like print statements or variable changes.

# Structure
<a name="description"></a>
A csvpath statement has three parts:
- A root that may include a file name
- The scanning part, that says what lines to validate
- The matching part, that decides if a line is valid

The root of a csvpath starts with `$`. The match and scan parts are enclosed by brackets. Newlines are ignored.

A very simple csvpath might look like this:

```bash
    $filename[*][yes()]
```

This csvpath says:
- Open the file: `filename`
- Scan all the lines: `*`
- And match every line scanned: `yes()`

In this case a match is considered a valid line. Treating matches as valid is a simple approach. There are <a href='https://www.csvpath.org/topics/validation' target='_blank'>many possible validation strategies</a> when its time to be more ambitious in your validation.

A slightly more functional csvpath could look like this:

```bash
    $people.csv[*][
        @two_names = count(not(#middle_name))
        last() -> print("There are $.variables.two_names people with only two names")]
```

This csvpath reads `people.csv`, counting the people without a middle name and printing the result after the last row is read.


# Validating Files
<a name="validating-files"></a>
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
    path = CsvPath().parse("""
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

<a name="grammar"></a>
## Grammars

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










