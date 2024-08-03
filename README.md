
# CsvPath

CsvPath defines a declarative syntax for inspecting and updating CSV files. Though much simpler, it is similar to:
- XPath: CsvPath is to a CSV file like XPath is to an XML file
- Schematron: Schematron validation is basically XPath rules applied using XSLT. CsvPath paths can be used as validation rules.
- CSS selectors: CsvPath picks out structured data in a conceptually similar way to how CSS selectors pick out HTML structures.

CsvPath is intended to fit with other DataOps and data quality tools. Files are streamed. The interface is simple. Custom functions can be added.

# Usage

CsvPath paths have three parts:
- a "root" file name
- a scanning part
- a matching part

The root starts with `$`. The match and scan parts are enclosed by brackets.

A very simple csvpath might look like this:

    $filename[*][yes()]

This path says open the file named `filename`, scan all the lines, and match every line scanned.

Learn <a href='docs/files.md'>more about filenames</a>.

## Running CsvPath

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

This is a very basic use of CsvPath. For more examples, see the unit tests.

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

Before we get into the scanning and matching parts of paths, including all the functions, let's look at print. The `print` function has several important uses, including:
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
<table>
<tr>
<td>Type</td>
<td>Returns</td>
<td>Matches</td>
<td>Description</td>
<td>Examples</td>
</tr>
    <tr>
        <td>Term </td>
        <td> Value </td>
        <td> True when used alone, otherwise calculated </td>
        <td>A quoted string or date, optionally quoted number, or
        regex. Regex features are limited. A regex is wrapped  in `/` characters and
only has regex functionality when used in the `regex()` function.</td>
        <td>
            <li/> "Massachusetts"
            <li/> 89.7
            <li/> /[0-9a-zA-Z]+!/
        </td>
    </tr>
    <tr>
        <td>Function </td>
        <td> Calculated   </td>
        <td> Calculated </td>
        <td>
            <a href='docs/functions.md'>Read about functions here</a>.
        </td>
        <td>
            <li/> not(count()==2)
            <li/> add( 5, 3, 1 )
            <li/> concat( end(), regex(#0, /[0-5]+abc/))
        </td>
    </tr>
    <tr>
        <td>Variable </td>
        <td>Value</td>
        <td>True when set unless `onchange`. Existence test when used alone, or with `asbool` the result is determined by treating the value as a bool.</td>
        <td>
            <a href='docs/variables.md'>Read about variables here</a>.
        </p>
        <td>
            <li/> @weather="cloudy"
            <li/> count(@weather=="sunny")
            <li/> #summer==@weather
            <li/> @happy.onchange=#weather
        </td>
    </tr>
    <tr>
        <td>Header     </td>
        <td>Value      </td>
        <td>Calculated. Used alone it is an existence test. The value can be tested as a bool value with `asbool` qualifier.  </td>
        <td>
            <a href='docs/variables.md'>Read about headers here</a>.
        </td>
        <td>
            <li/> #firstname
            <li/> #"My firstname"
            <li/> #3
        </td>
    </tr>
    <tr>
        <td>Equality</td>
        <td>Calculated   </td>
        <td>True at assignment, otherwise calculated   </td>
        <td>Two of the other types joined with an "=" or "==".</td>
        <td>
            <li/> `@type_of_tree="Oak"`
            <li/> `#name == @type_of_tree`
        </td>
    </tr>
<table>

## Qualifiers

Variables and some functions can take qualifiers on their name. A qualifier takes the form of a dot plus a qualification name. At the moment there are only four qualifiers:

- `onmatch` to indicate that action on the variable or function only happens when the whole path matches a row
- `onchange` set on a variable to indicate that a row should only match when the variable is set to a new value
- `asbool` set on a variable or header to have its value interpreted as a bool rather than just a simple `is not None` test
- `nocontrib` set on the left hand side of a `->` to indicate that there should be no impact on the row match. E.g. `$test[*][yes() last.nocontrib() -> print("last line!")]` will collect all rows but only print on the last; whereas, without `nocontrib` only the last line would be collected.
- An arbitrary string to add a name for the function's internal use, typically to name a variable

Qualifiers look like:

    [ @myvar.onmatch = yes() ]

Or:

    [ @i = increment.this_is_my_increment.onmatch(yes(), 3) ]

When multiple qualifiers are used order is not important.

Qualifiers are actively being discovered and implementation is opportunistic. Eventually the feature will need to be formalized. Watch this space!

## The when operator

`->`, the "when" operator, is used to act on a condition. `->` can take an equality or function on the left and trigger an equality, assignment, or function on the right. For e.g.

    [ last() -> print("this is the last line") ]

Prints `this is the last line` just before the scan ends.

    [ exists(#0) -> @firstname = #0 ]

Says to set the `firstname` variable to the value of the first column when the first column has a value.

## Another Example
    [ exists(#common_name) #0=="field" @tail.onmatch=end() not(in(@tail, 'short|medium')) ]

In the path above, the rules applied are:
- The exists test of `#common_name` checks if the column with the header "common_name" has a value. Headers are named for whatever values are found in the 0th row. They indicate a column in the row being checked for match.
- `#2` means the 3rd column, counting from 0
- Functions and column references are ANDed together
- `@tail` creates a variable named "tail" and sets it to the value of the last column if all else matches
- Functions can contain functions, equality tests, and/or literals

# Not Ready For Production
Anything could change and performance could be better. This project is a hobby.













