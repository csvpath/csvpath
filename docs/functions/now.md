
# Now

Returns the current datetime, optionally formatted. now() uses [strftime()](https://strftime.org/).

You can also use these aliases:
- `thisyear()` - same as `now("%Y")`
- `thismonth()` - same as `now("%m")`
- `today()` - same as `now("%d")`

## Example

    $file.csv[*][now("%Y") == "2024"]





