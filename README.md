
# CsvPath

CsvPath defines a declarative syntax for inspecting and updating CSV files. It is similar, though much simpler, to:
- XPath: CsvPath is to a CSV file like XPath is to an XML file
- Schematron: Schematron is basically XPath rules applied using XSLT. CsvPath paths can be used as validation rules.
- CSS selectors: CsvPath picks out structured data in a similar way to how CSS selectors pick out HTML structures.

CsvPath is intended to fit with other DataOps and data quality tools. Files are streamed. The interface is simple. Custom functions can be added.

# Usage
CsvPath paths have three parts, scanning, matching, and modifying. Today, only the scanning and matching parts of CsvPath are functional. The modification part is a todo.

For usage, see the unit tests in [tests/test_scanner.py](tests/test_scanner.py), [tests/test_matcher.py](tests/test_matcher.py) and [tests/test_functions.py](tests/test_functions.py).

    path = CsvPath(delimiter=",")
    path.parse("$test.csv[5-25][#0="Frog" #lastname="Bats" count()=2]")
    for i, line in enumerate( path.next() ):
        print(f"{i}: {line}")

    print(f"path vars: {path.variables}")

This scanning and matching path says:
- open test.csv
- scan lines 5 through 25
- match the second time we see a line where the first column equals "Frog" and the column called  "lastname" equals "Bats"

# Scanning
The scanner enumerates lines. For each line returned, the line number, the scanned line count, and the match count are available. The set of line numbers scanned is also available.

The scan part of the path starts with '$' to indicate the root, meaning the file from the top. After the '$' comes the file path. The scanning instructions are in a bracket. The rules are:
- `[*]` means all
- `[3*]` means starting from line 3 and going to the end of the file
- `[3]` by itself means just line 3
- `[1-3]` means lines 1 through 3
- `[1+3]` means lines 1 and line 3
- `[1+3-8]` means line 1 and lines 3 through eight

# Matching
The match part is also bracketed. The rules are:
- `#animal` indicates a header named "animal". Headers are the values in the 0th line.
- `#2` means the 3rd column, counting from 0
- A column reference with no equals or function is an existence test
- Functions and column references are ANDed together
- `@people` denotes a variable named "people"
- Functions can contain functions, equality tests, and/or literals
- Limited arithmetic is available. For e.g. `@number_of_cars = 2 + count() + @people`. Four operations are supported: `+`, `-`, `*`, and `/`. Arithmetic is not fully baked and is off by default. The `add()`, `subtract()`, `multiply()` and `divide()` functions should be preferred.

The match functions are:

| Function                      | What it does                                              |Done|
|-------------------------------|-----------------------------------------------------------|----|
| add(value, value, ...)        | adds numbers                                              | X  |
| after(value)                  | finds things after a date, number, string                 | X  |
| average(number, type)         | returns the average up to current "line", "scan", "match" | X  |
| before(value)                 | finds things before a date, number, string                | X  |
| concat(value, value)          | counts the number of matches                              | X  |
| count()                       | counts the number of matches                              | X  |
| count(value)                  | count matches of value                                    | X  |
| count_lines()                 | count lines to this point in the file                     | X  |
| count_scans()                 | count lines we checked for match                          | X  |
| divide(value, value, ...)     | divides numbers                                           | X  |
| end()                         | returns the value of the last column                      | X  |
| every(number, value)          | match every Nth time a value is seen                      |    |
| first(value)                  | match the first occurrence and capture line               | X  |
| in(value, list)               | match in a list                                           | X  |
| increment(value, n)           | increments a variable by n each time seen                 |    |
| isinstance(value, typestr)    | tests for "int","float","complex","bool","usd"            | X  |
| length(value)                 | returns the length of the value                           | X  |
| lower(value)                  | makes value lowercase                                     | X  |
| max(value, type)              | largest value seen up to current "line", "scan", "match"  | X  |
| median(value, type)           | median value up to current "line", "scan", "match"        | X  |
| min(value, type)              | smallest value seen up to current "line", "scan", "match" | X  |
| multiply(value, value, ...)   | multiplies numbers                                        | X  |
| no(value)                     | always false                                              | X  |
| not(value)                    | negates a value                                           | X  |
| now(format)                   | a datetime, optionally formatted                          | X  |
| or(value, value,...)          | match any one                                             | X  |
| percent(type)                 | % of total lines for "scan", "match", "line"              | X  |
| random(list)                  | pick from a list                                          |    |
| random(starting, ending)      | generates a random int from starting to ending            | X  |
| regex(regex-string)           | match on a regular expression                             | X  |
| subtract(value, value, ...)   | subtracts numbers                                         | X  |
| then(y,m,d,hh,mm,ss,format)   | a datetime, optionally formatted                          |    |
| upper(value)                  | makes value uppercase                                     | X  |

# Modification (coming soon!)
The modification part of a CsvPath is also wrapped in brackets. This part of the path modifies any matching row. A modifying path (line breaks are permitted between parts) looks like:

`$test.csv[5-25]`
`[#0="Frog" #lastname="Bats" count()=2]`
`[#1="make my speed 6" #zipcode>#last_four #last_four=random(int, 4)]`

This path's modification part says:
- set the first column to 'make my speed 6'
- add a last_four column after zipcode (this obviously affects all rows, not just the matched ones)
- set the value of the last_four column where the path matches to a random 4-character integer

Note that the creating of the last_four column and setting its value may be order-dependent. That has not been decided yet. It may needed to involve multiple paths.

To output a new file, either with or without making a modified copy of the original, do something like:

`$test.csv[5-25]`
`[#0="Frog" #lastname="Bats"]`
`[out($newfile.csv, #1=Firstname=#firstname)
  out($newfile.csv, #0=Surname=#lastname)
  out($newfile.csv, #2=ID=random("int")
  out($newfile.csv, #3=Line=count-lines())
 ]`

This path creates a file with 4 columns, in this order: {Surname, Firstname, ID, Line}, and fills it using the matched lines in the original file. The out() function sends its output to the referenced file, in this case $newfile.csv. Any changes to the existing file's copy-on-write update are done after the out() function outputs the existing information. That allows us to change the file we are scanning and also keep a record of the changes we make.

The modification basics are:
- `#say='hoo!'` means set the value of the column with the "say" header to "hoo!"
- variables, indicated by a leading '@', that were set in the matching part can be used in the modification part
- `$[@line]#3="cactus"` means a set the 4th column (zero-based) value to "cactus" in the row indicated by the variable @line in the current file, indicated with the '$'
- `#1>"n/a"` adds a new column following the 2nd column (zero-based) with the value in that row being 'n/a'
- `#firstname>#lastname="fred"` adds a "lastname" column after the "firstname" column and gives the matched row the value "fred"
- `#NumberOfFreds="this is fred @n"` means set the column with the header "NumberOfFreds" to the string using value of the @n variable. Presumably in the matching part we had declared something like `[#firstname="fred" @n=count()]`.
- `#|=>#cactus=""` means add a column after the last column, whatever number column it may be, with the header "cactus" and no value entered. The "|" indicates the ending column. The "=>" says add a column. #cactus is the header given to the new column. And ="" says don't assign a value. Or you could simply say: `#|=>#cactus` to do the same
- `#^=>#cactus="prickly pear"` does the same but creating a new first column named "cactus" and setting the value of matched rows to "prickly pear". This new column is the new #0 column and the old #0 column is now #1.
- `_|=>#0="fussy bug" #1="furry fly" #3=4.45 #|=>"last column"` says add a new row, `=>`, at the end of the file, `_|` and set the columns to the values indicated with the last column, whatever number it might be, to the value "last column".
- `1^=>` or `^=>` mean add a new blank row above this row.
- `2v=>` means add two new blank rows below this row.

CsvPath is a copy-on-write system. When you make a modification, it creates a copy of the file you are reading rows from. The copy has any modifications you make while the original is untouched. In order to do this, CsvPath needs to set a window around the current row. If you open a CsvPath using a 10-line window, the changes you make must be within 10 rows of the currently matched row.


# Not Ready For Production
Anything could change. This project is a hobby.













