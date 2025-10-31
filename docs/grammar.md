
# CsvPath Grammar

Several parsers handle different parts of CsvPath Framework.

CsvPath Validation Lanaguage parsing has four parts:
- [The matching part](https://github.com/csvpath/csvpath/blob/main/csvpath/matching/lark_parser.py)
- [The scanning part](https://github.com/csvpath/csvpath/blob/main/csvpath/scanning/scanner2_parser.py)
- [The `print()` parser](https://github.com/csvpath/csvpath/blob/main/csvpath/matching/util/lark_print_parser.py)
- Metadata fields parsing

CsvPath Reference Language is the pointer/query language supporting the Framework's file handling and Validation Language's references data type.
- [QueryParser](https://github.com/csvpath/csvpath/blob/main/csvpath/util/references/reference_grammar.py)



