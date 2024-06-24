
# CsvPath

CsvPath is a declarative syntax for identifying rows and column values and updating them. It is similar to:
- XPath: CsvPath is to a CSV file like XPath is to an XML file
- Schematron: Schematron is basically XPath rules applied using XSLT. CsvPath can be used as validation rules.
- CSS selectors: CsvPath picks out structured data in a similar way to how CSS selectors pick out HTML structures.

# Usage
Today, only the scanning and matching parts of csvpath are complete. The modification part is a todo.

For usage, see the unit tests in [tests/test_scanner.py](tests/test_scanner.py) or [tests/test_matcher.py](tests/test_matcher.py). In brief, do:
    from csvpath.csvpath import CsvPath
    csvpath = CsvPath()
    scanner = csvpath.parse(f'$test.csv[5-25][#0="Frog" #lastname="Bats" count()=2]')
    for line in scanner.next():
        print(f"a {line}")

This path says:
- open test.csv
- scan lines 5 through 25
- match the second time we see a line where the first column equals "Frog" and the column called  "lastname" equals "Bats"

The scanner is enumerable. For each line enumerated the line number, the scanned line count, and the match count are available. The set of line numbers scanned are also available.

The path syntax is broken into three parts:
- The scan part
- The match part (not yet complete), and
- The modify part (not yet started)

The scan part of the path starts with '$' to indicate the root, meaning the file from the top. After the '$' comes the file path. The scanning instructions are in a bracket. The rules are:
- * means all
- 3* means starting from line 3 and going to the end of the file
- 3 by itself means just line 3
- 1-3 means lines 1 through 3
- 1+3 means lines 1 and line 3
- 1+3-8 means line 1 and lines 3 through eight

The match part is also bracketed. The rules are:
- #animal indicates a header named "animal". Headers are the 0 line
- #2 means the 3rd column, counting from 0
- A column reference with no equals or function is an existance test
- Functions and column references are ANDed together
- @people denotes a variable named "people"
- Functions can include functions and equality tests

At this time the working functions are:
- count()
- regex()

Planned functions include:

    | Function                      | What it does                                  |
    | ------------------------------|-----------------------------------------------|
    | count()                       | number of matches                             |
    | count(value)                  | count matches of value                        |
    | regex(regex-string)           | match on a regular expression                 |
    | now()                         | a date                                        |
    | not(value)                    | negates a value                               |
    | type()                        | returns the type of a field                   |
    | length(value)                 | returns the length of the value               |
    | count-scanned()               | count lines we checked for match              |
    | count-lines()                 | count lines to this point in the file         |
    | lower(value)                  | makes value lowercase                         |
    | upper(value)                  | makes value uppercase                         |
    | after(value)                  | finds things after a date, number, string     |
    | before(value)                 | finds things before a date, number, string    |
    | between(from, to)             | between dates, numbers, strings, %, $         |
    | random(type, from, to)        | random number, string, or date within a range |
    | random(list)                  | pick from a list                              |
    | in(list-source)               | match in a list from a file                   |
    | or(value, value...)           | match one                                     |
    | every(number, value)          | match every n times a value is seen           |


















