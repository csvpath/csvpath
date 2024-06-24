
# CsvPath

CsvPath is a declarative syntax for identifying rows and column values and updating them. It is similar to:
- XPath: CsvPath is to a CSV file like XPath is to an XML file
- Schematron: Schematron is basically XPath rules applied using XSLT. CsvPath can be used as validation rules.
- CSS selectors: CsvPath picks out structured data in a similar way to how CSS selectors pick out HTML structures.

# Usage
See the unit tests in tests/test_scanner.py or tests/test_matcher.py. In brief, do:
csvpath = CsvPath()
scanner = csvpath.parse(f'$test.csv[2-5][#0="Frog" #lastname="Bats" count()=2]')

This path says:
- open test.csv
- scan lines 2 through 5
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

At this time the functions are:
- count()
- regex()



















