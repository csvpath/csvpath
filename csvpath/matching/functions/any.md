
# Any

Finds values in any column or variable.

Find comes in the following forms:

|------------------------|------------------------------------------------------------|
|any()                   | True if any header or variable would return a value |
|any(header())           | True if any header would return a value               |
|any(variable())         | True if any variable would return a value        |
|any(value)              | True if the value can be found in any header or variable   |
|any(header(), value)    | True if the value can be found in any header         |
|any(variable(), value)  | True if the value can be found in any variable   |


## Examples

    $file.csv[*][any(header())]

Are any columns populated? This is the same as naming all the headers in an or().

    $file.csv[*][any(variable(), "fish")]

True if any variable has the value `fish`.



