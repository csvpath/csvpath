
# Terms

A term is just a scalar or token. Terms are limited to being:
- Quoted strings
- Ints
- Floats
- Regular expressions

The CsvPath libary's grammar is built up from regular expression-based tokens. (It uses <a href='https://ply.readthedocs.io/en/latest/'>Ply</a>). The lexer is limited; although, a future release may expand the grammar and make certain elements, like terms, more flexible. Today the CsvPath lexer's term definition regexes are:

- Strings: `r'"[\$A-Za-z0-9\.%_|\s :\\/,]+"'`
- Numbers: `r"\d*\.?\d+"`
- Regex: `r"/(?:[^/\\]|\\.)*/"`

Anything that matches these expressions is acceptable.

The regex functionality term supports within csvpaths is limited. Regexes only act as a regex when they are used within the `regex()` function.

# Examples:

- `"a quoted string"`
- `3.5`
- `.5`
- `3`
- `regex( /a [r|R]egex\??/, #aheader )`


