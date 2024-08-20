
# CsvPath Grammar

The CsvPath grammar is a work in progress, mainly on the match side. You can see the current versions of the parsers in Scanner and the new <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/lark_parser.py'>LarkParser</a>.

There is a big pile of mostly pretty nonsensical match parts of csvpaths <a href='https://github.com/dk107dk/csvpath/blob/main/tests/grammar/match'>here</a>. They are are automatically pulled from the unit tests and used to double check the match parser.

Due to development choices over time, matching is currently handled by <a href='https://lark-parser.readthedocs.io/en/latest/'>Lark</a> and scanning by <a href='https://www.dabeaz.com/ply/ply.html'>Ply</a>. That division of labor is likely to change in the near future. Regardless, scanning and matching will probably each continue to be handled by its own parser.

The CsvPath grammar is under active development.

