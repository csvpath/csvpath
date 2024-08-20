
# CsvPath Grammar

The CsvPath grammar is a work in progress. You can see the current versions in Scanner and the new <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/lark_parser.py'>LarkParser</a>.

Due to development choices over time, matching is handled by <a href='https://lark-parser.readthedocs.io/en/latest/'>Lark</a> and scanning by <a href='https://www.dabeaz.com/ply/ply.html'>Ply</a>. That division of labor is likely to change in the near future. Regardless, scanning and matching will probably each continue to be handled by its own parser.



