
# CsvPath

CsvPath is a declarative syntax for identifying rows and column values and updating them. It is similar to:
- XPath: CsvPath is to a CSV file like XPath is to an XML file
- Schematron: Schematron is basically XPath rules applied using XSLT. CsvPath can be used as validation rules.
- CSS selectors: CsvPath picks out structured data in a similar way to how CSS selectors pick out HTML structures.

# Usage
Today, only the scanning and matching parts of csvpath are complete. The modification part is a todo.

For usage, see the unit tests in [tests/test_scanner.py](tests/test_scanner.py) or [tests/test_matcher.py](tests/test_matcher.py). In brief, do:
`    from csvpath.csvpath import CsvPath`
`    csvpath = CsvPath()`
`    scanner = csvpath.parse(f'$test.csv[5-25][#0="Frog" #lastname="Bats" count()=2]')`
`    for line in scanner.next():`
`        print(f"a {line}")`

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
- `[*]` means all
- `[3*]` means starting from line 3 and going to the end of the file
- `[3]` by itself means just line 3
- `[1-3]` means lines 1 through 3
- `[1+3]` means lines 1 and line 3
- `[1+3-8]` means line 1 and lines 3 through eight

The match part is also bracketed. The rules are:
- `#animal` indicates a header named "animal". Headers are the values in the 0th line.
- `#2` means the 3rd column, counting from 0
- A column reference with no equals or function is an existence test
- Functions and column references are ANDed together
- `@people` denotes a variable named "people"
- Functions can include functions and/or equality tests and/or literals, all represented by the word "value" in the table below

At this time the working functions are:
- `count()` and `count(value)`
- `regex()`

The full set of planned functions is:

| Function                      | What it does                                  |
| ------------------------------|-----------------------------------------------|
| count()                       | counts the number of matches                  |
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
| in(list)                      | match in a list                               |
| or(value, value...)           | match one                                     |
| every(number, value)          | match every Nth time a value is seen          |

#Modification (coming soon!)
The modification part of a CsvPath is not wrapped in brackets. This part of the path modifies any matching row. The basics are:
- `#say='hoo!'` means set the value of the column with the "say" header to "hoo!"
- variables, indicated by a leading '@', that were set in the matching part can be used in the modification part
- `$[@line]#3="cactus"` means a set the 3rd column value to "cactus" in the row indicated by the variable @line in the current file, indicated with the '$'
- `#1>"n/a"` adds a new column following the 2nd column (zero-based!) with the value in that row being 'n/a'
- `#firstname>#lastname="fred"` adds a "lastname" column after the "firstname" column and gives the matched row the value "fred"
- `#NumberOfFreds="this is fred @n"` means set the column with the header "NumberOfFreds" to the value of the @n variable. Presumably in the matching part we had declared something like `[#firstname="fred" @n=count()]`.
- `#|>#cactus=""` means add a column after the last column, whatever number column it may be, with the header "cactus" and no value entered. The "|" indicates the ending column. The ">" say add a column. #cactus is the header given to the new column. And ="" says don't assign a value. Or you could simply say: `#|>#cactus` to do the same
- .^>#cactus="prickly pear" does the same but creating a new first column named "cactus" and setting the value of matched rows to "prickly pear". This new column is the new #0 column and the old #0 column is now #1.

#All that could change!!
In fact, anything could change. This project hobby.













