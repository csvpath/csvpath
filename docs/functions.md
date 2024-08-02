
# Functions

Functions perform work within a csvpath. A function is represented by a name followed by parentheses.

There are dozens of functions that are outlined elsewhere. More functions can be easily created; although, at the moment there is not yet a simple way to incorporate external code as a new function without changing the CsvPath codebase.

Functions can contain:
- terms
- variables
- headers
- equality tests
- variable assignment
- other functions

Some functions take a specific or unlimited number of types as arguments.

Certain functions have qualifiers. An `onmatch` qualifier indicates that
the function should be applied only when the whole path matches.

Some functions optionally will make use of an arbitrary name qualifier to better name a tracking variable.
Qualifiers are described elsewhere.

# Examples
- `not(count()==2)`
- `add( 5, 3, 1 )`
- `concat( end(), regex(#0, /[0-5]+abc/))`

