
# Date and Datetime

Returns a date or datetime object for a value given a format string.

`date()` uses [strftime()](https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior).

`datetime()` also uses strftime.

## Example

```bash
    $file[*][ after( date(#date_joined,"%Y-%m-%d"), date("2021-12-31", "%Y-%m-%d")) ]
```

Matches if the `date_joined` header value is after the 31st of December, 2021.




