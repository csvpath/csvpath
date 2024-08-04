
# CsvPath

CsvPath defines a declarative syntax for inspecting and updating CSV files. Though much simpler, it is inspired by:

- XPath. CsvPath is to CSV files like XPath is to XML files.
- Validation of XML using Schematron rules
- The way CSS selectors pick out HTML structures

CsvPath is intended to fit with other DataOps and data quality tools. Files are streamed. The interface is simple. Custom functions can be added.

# Description

CsvPath paths have three parts:
- a "root" file name
- a scanning part
- a matching part

The root starts with `$`. The match and scan parts are enclosed by brackets. Newlines are ignored.

A very simple csvpath might look like this:

    $filename[*][yes()]

This path says open the file named `filename`, scan all the lines, and match every line scanned.

A slightly more functional csvpath could look like this:

    $people.csv[*][
         @two_names = count(not(#middle_name))
         last() -> print("There are $.variables.two_names people with only two names")]

This path reads `people.csv`, counting the people without a middle name and printing the result after the last row is read.

See [more examples here](#examples).

There is no limit to the amount of functionality you can include in a single csvpath. However, different functions run with their own performance characteristics. You should plan to test both the performance and functionality of your paths.

CsvPath was conceived as a data testing and extraction tool. The assumption was that using csvpaths would typically involve testing the paths in advance and then using them in automated runs.

Interactive use of csvpaths can be valuable, too, of course. There is a simple REPL (read–eval–print loop) script at the project's root (<a href='repl.py'>repl.py</a>) that you can use to explore and test csvpaths.

## Running CsvPath

CsvPath is <a href='https://pypi.org/project/csvpath/'>available on Pypi here</a>.

Two classes do all the work: CsvPath and CsvPaths. Each has only a few external methods.
- CsvPath
  - parse(pathstring) applies a csvpath
  - next() iterates over the matched rows returning each matched row as a list
  - fast_forward(int) processes n rows
  - collect(int) processes n rows and collects the lines that matched as lists
- CsvPaths
  - csvpath() gets a CsvPath that knows all the file names available
  - set_named_files(Dict[str,str]) sets the file names as a dict of named paths
  - set_file_path(str) sets the file names from:
    - a JSON file of named paths or
    - a single .csv file or
    - a directory of .csv files

There are several ways to set up csvpath file references. Read <a href='docs/files.md'>more about filenames</a>.

This is a very basic programmatic use of CsvPath. For lots more examples, see the unit tests.

    path = CsvPath()
    path.parse("""$test.csv[5-25]
                    [
                        #0=="Frog"
                        @lastname.onmatch="Bats"
                        count()==2
                    ]
               """)
    for i, line in enumerate( path.next() ):
        print(f"{i}: {line}")
    print(f"path vars: {path.variables}")

The csvpath says:
- Open test.csv
- Scan lines 5 through 25
- Match the second time we see a line where the first column equals "Frog" and set the variable called  "lastname" to "Bats"

Another path that does the same thing a bit more simply might look like:

    """$test.csv[5-25]
        [
            #0=="Frog"
            @lastname.onmatch="Bats"
            count()==2 -> print( "$.match_count: $.line")
        ]
    """

In this case we're using the "when" operator, `->`, to determine when to print.


## The print function

Before we get into the details of the scanning and matching parts of paths, including all the functions, let's look at print. The `print` function has several important uses, including:

- Debugging csvpaths
- Validating CSV files
- Creating new CSV files based on an existing file

### Validating CSV

CsvPath paths can be used for rules based validation. Rules based validation checks a file against content and structure rules but does not validate the file's structure against a schema. This validation approach is similar to XML's Schematron validation, where XPath rules are applied to XML.

There is no "standard" way to do CsvPath validation. The simplest way is to create csvpaths that print a validation message when a rule fails. For example:

    $test.csv[*][@failed = equals(#firstname, "Frog")
                 @failed.asbool -> print("Error: Check line $.line_count for a row with the name Frog")]

Several rules can exist in the same csvpath for convenience and/or performance. Alternatively, you can run separate csvpaths for each rule.

### Creating new CSV files

Csvpaths can use the `print` function to generate new file content on system out. Redirecting the output to a file is an easy way to create a new CSV file based on an existing file. For e.g.

    $test.csv[*][ line_count()==0 -> print("lastname, firstname, say")
                  above(line_count(), 0) -> print("$.headers.lastname, $.headers.firstname, $.headers.say")]

This csvpath reorders the headers of the test file at `tests/test_resources/test.csv`. The output file will have a header row.


# Scanning
The scanner enumerates lines. For each line returned, the line number, the scanned line count, and the match count are available. The set of line numbers scanned is also available.

The scan part of the path starts with a dollar sign to indicate the root, meaning the file from the top. After the dollar sign comes the file path. The scanning instructions are in a bracket. The rules are:
- `[*]` means all
- `[3*]` means starting from line 3 and going to the end of the file
- `[3]` by itself means just line 3
- `[1-3]` means lines 1 through 3
- `[1+3]` means lines 1 and line 3
- `[1+3-8]` means line 1 and lines 3 through eight

# Matching
The match part is also bracketed. Matches have space separated components or "values" that are ANDed together. The components' order is important. A match component is one of several types:

- Term
- Function
- Variable
- Header
- Equality

## Term
A string, number, or regular expression value.

|Returns | Matches | Examples      |
|--------|---------|---------------|
|A value | Always true | `"a value"` |

<a href='docs/terms.md'>Read about terms here</a>.

## Function
A composable unit of functionality called once for every row scanned.

|Returns | Matches | Examples      |
|--------|---------|---------------|
|Calculated | Calculated | `count()` |

<a href='docs/functions.md'>Read about functions here</a>.

## Variable
A stored value that is set or retrieved once per row scanned.

|Returns | Matches | Examples      |
|--------|---------|---------------|
|A value | True when set, unless `onchange`. Used alone it is an existence test. | `@firstname` |

<a href='docs/variables.md'>Read about variables here</a>.

## Header

A named column or a column identified by 0-based index.

|Returns | Matches | Examples      |
|--------|---------|---------------|
|A value | Calculated. Used alone it is an existence test. | `#area_code` |

<a href='docs/variables.md'>Read about headers here</a>.

## Equality
Two of the other types joined with an "=" or "==".

|Returns | Matches | Examples      |
|--------|---------|---------------|
|Calculated | True at assignment, otherwise calculated. | `#area_code == 617` |

## Comments

You can comment out components of a csvpath's match part using wrapping `~`. Comments can be multi-line. At the moment the only limitations are:

- Comments cannot follow one directly after another
- Comments cannot go within match components, only between them

Examples:

    [ count() ~ this is a comment~ ]
    [ ~this path is
       just experimental ~ any() ]


## The when operator

`->`, the "when" operator, is used to act on a condition. `->` can take an equality or function on the left and trigger an equality, assignment, or function on the right. For e.g.

    [ last() -> print("this is the last line") ]

Prints `this is the last line` just before the scan ends.

    [ exists(#0) -> @firstname = #0 ]

Says to set the `firstname` variable to the value of the first column when the first column has a value.

## Qualifiers

Qualifiers are tokens added to variable, header, and function names. They are separated from the names and each other with `.` characters. Each qualifier causes the qualified match component to behave in a different way than it otherwise would.

<a href='docs/qualifiers.md'>Read about qualifiers here.</a>

<a name="examples"></a>
## More Examples

    [ exists(#common_name) #0=="field" @tail.onmatch=end() not(in(@tail, 'short|medium')) ]

In the path above, the rules applied are:
- The exists test of `#common_name` checks if the column with the header "common_name" has a value. Headers are named for whatever values are found in the 0th row. They indicate a column in the row being checked for match.
- `#2` means the 3rd column, counting from 0
- Functions and column references are ANDed together
- `@tail` creates a variable named "tail" and sets it to the value of the last column if all else matches
- Functions can contain functions, equality tests, and/or terms.

There are more examples scattered throughout the documentation. Good places to look include:

- The individual <a href='docs/functions.md'>function descriptions</a>
- The <a href='tests'>unit tests</a> _(not realistic, but a good source of ideas)_
- A few <a href='docs/examples.md'>more real-looking examples</a>

# Not Ready For Production
Anything could change and performance could be better. This project is a hobby.













