
# Terms

A term is just a scalar or token. Terms are limited to being:
- Quoted strings
- Ints
- Floats
- Regular expressions

The CsvPath libary's grammar is built up from regular expression-based. (It uses <a href='https://ply.readthedocs.io/en/latest/'>Ply</a>). The lexer is limited; although, a future release may expand the grammar and make certain elements, like terms, more flexible. Today the term regexes are:

- Strings: r'"[\$A-Za-z0-9\.%_|\s :\\/,]+"'
- Numbers: r"\d*\.?\d+"
- Regex: r"/(?:[^/\\]|\\.)*/"

The regex functionality is limited and only acts as a regex when used within the `regex()` function.

# Examples:

- "a quoted string"
- 3.5
- .5
- 3
- /a [r|R]egex\??/


