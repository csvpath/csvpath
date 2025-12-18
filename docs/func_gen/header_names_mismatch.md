
Header names mismatch

Given a | delimited list of headers, checks that all exist and are in
the same order.

While the function is intended for matching, substantial data is
created in variables. The following variables containing header names
may be useful:

- N_present

- N_unmatched

- N_misordered

- N_duplicated

(Where 'N' is a name qualifier, if given, or 'header_names_mismatch')

If you have: header_names_mismatch.m("Alpha|Beta|Cappa|Delta") and
your headers are: Alpha,Delta,Beta you will have @m_present ==
["Alpha"], @m_unmatched == ["Cappa"], @m_misordered = ["Delta"] and
header_names_mismatch() will return False; i.e. not match.

Note that the alias header_names_mismatch() is depreciated. Instead
use header_names_match(). The name change reflects the function's
match value being false if the headers do not meet expectations.

| Data signatures                                      |
|:-----------------------------------------------------|
| header_names_mismatch( pipe delimited headers: str ) |

| Call signatures                                       |
|:------------------------------------------------------|
| header_names_mismatch( pipe delimited headers: Term ) |

| Purpose    | Value                                               |
|:-----------|:----------------------------------------------------|
| Main focus | header_names_mismatch() produces a calculated value |
| Aliases    | header_names_mismatch, header_names_match           |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |


