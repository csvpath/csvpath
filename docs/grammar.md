
# CsvPath Grammar

Four parsers handle different parts of CsvPath parsing:
- The match part
- The scanning part
- Wrapping comments
- `print()`

You can see the current versions of the parsers in the Scanner module and <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/lark_parser.py'>LarkParser</a>.

There is a big pile of mostly pretty nonsensical match parts of csvpaths <a href='https://github.com/dk107dk/csvpath/blob/main/tests/grammar/match'>here</a>. They are are automatically pulled from the unit tests and used to double check the match parser.

Due to development results over time, matching and printing are handled by <a href='https://lark-parser.readthedocs.io/en/latest/'>Lark</a> and scanning by <a href='https://www.dabeaz.com/ply/ply.html'>Ply</a>. Comment parsing does not have a grammar.

Until the 1.0 release CsvPath grammar should be assumed to be under active development.

