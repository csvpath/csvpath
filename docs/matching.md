<a name="matching"></a>

# Matching

The matching part is the third and last part of a csvpath. It comes behind the root and the scanning part. Like the scanning part, it is bracketed. The matching part is where validation and/or data upgrading happens.

## Match Components

The matching part is built from space separated "match components" that are ANDed or ORed together. When a match component "votes" to match its value is True. That means as far as that match component is concerned, the line matches.

Csvpaths are configured to logically AND match components together by default. When match components are ANDed, all the components must match for the line to match as a whole. When the components are ORed, if any one match component matches the line is considered to match.

Csvpaths may be configured so that matched lines are:
* Considered valid or invalid
* Collected as output from evaluation

The match components' order is meaningful. Generally, components are tested left to right, top to bottom. The exception to this order is if a match component is set to only match if all other components match. In that case, that match component must come last. If all match components are set to only match if all other match components match, the order of all the components is preserved.

## Types of Match Components

A match component is one of these types:

- [Term](#term)
- [Function](#function)
- [Variable](#variable)
- [Header](#header)
- [Equality](#equality)
- [Reference](#reference)

These components can be combined in endless ways. The organization of a csvpath's match part is `[x x x x]` where each `x` is a match component. All of the match components are ANDed or ORed together. There can be any number of match components in a csvpath statement.

Since equalities are match components, `[ "x" == "y" "z" == "z" ]` is a legal csvpath matching part containing two top-level match components. Each of those two components is an Equality. Each Equality holds two Term component literals, `"x"` and `"y"`, and `"z"` and `"z"`.

In this case, if the csvpath ANDs match components, the default, this statement will never match because `"x"` never equals `"y"`. If evaluation is switched to OR, the statement will always match because `"z"` always equals `"z"`. The switch from AND to OR can be done programmatically or, more typically, using a mode declaration in a csvpath comment. Modes are covered in the page on comments.

## Qualifiers

Some of these component types can be modified with qualifiers. A qualifier changes the behavior of a match component. It is set by adding a dot-name to the match component name.

For example, `count.cars(#color=="blue")` is a variation on `count(#color=="blue")`. The difference is that behind the scenes the `count()` function's variable is named `cars`, rather than a random string. Likewise `count.cars.onmatch(#color=="blue")` increments the count of the `cars` variable only if the rest of the line matches.

[Read more about qualifiers here](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md).

## Testing Required

There is no limit to the functionality you can include in a single csvpath using match components. However, functions have different performance characteristics. You should test both the performance and functionality of your paths, just as you would when working with SQL or another language.


<a name="Components"></a>

# Match Component Types

<a name="term"></a>

## Term

A string, number, or regular expression value.

<table>
    <thead>
        <tr>
            <th>
                Returns
            </th>
            <th>
                Matches
            </th>
            <th>
                Examples
            </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>
                A value
            </td>
            <td>
                Always matches
            </td>
            <td>
                <ul>
                    <li/> <code>"a value"</code>
                    <li/> <code>3</code>
                </ul>
            </td>
        </tr>
    </tbody>
</table>


<a href='https://github.com/dk107dk/csvpath/blob/main/docs/terms.md'>Read about terms here</a>.


<a name="function"></a>

## Function

A composable unit of functionality called once for every row scanned. CsvPath Validation Language has over 150 functions. As a language, it is very much functions-oriented.

|Returns    | Matches    | Examples      |
|-----------|------------|---------------|
|Calculated | Calculated | `count()`     |

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions.md'>Read about functions here</a>.


<a name="variable"></a>

## Variable

A value that is set or retrieved once per row scanned. Generally, variables last from the line they are created on through the end of the file. Variables are available at the end of evaluation.

|Returns | Matches | Examples      |
|--------|---------|---------------|
|A value | True when set. (Unless the `onchange` qualifier is used). Alone a variable is an existence test. | `@firstname` |

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/variables.md'>Read about variables here</a>.


<a name="header"></a>

## Header

A named header or a header identified by its 0-based index.
_(CsvPath avoids the word "column" for reasons we'll go into later)._

|Returns | Matches | Examples      |
|--------|---------|---------------|
|A value | Calculated. Used alone it is an existence test. | `#area_code` |

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/headers.md'>Read about headers here</a>.


<a name="equality"></a>

## Equality

Two of the other match component types joined with an "=" or "==" or the when-do operator `->`.

|Returns | Matches | Examples      |
|--------|---------|---------------|
|Calculated | Calculated | `#area_code == 617` |
|Calculated | When-do matches when left side matches | `#area_code -> print("area code is $.headers.area_code")` |
|No value | Assignment always matches | `@code = #area_code` |


<a name="reference"></a>

## Reference

References are a way of pointing to data generated by other csvpaths. Referenced data is held by a `CvsPaths` class instance. It is stored as its named-results. The name is the one that identified the named-paths group that generated it.

Within csvpaths, references can point to:
- Variables
- Headers
- Csvpath runtime indicators

A csvpath runtime indicator is a metric or fact about the running csvpath. These include things like the line count, the start time, if the file is considered valid, etc.

References are also used more broadly outside of csvpaths for data and run management. That topic is covered on [csvpath.org](https://www.csvpath.org).

The form of a reference is:

```bash
    $my-name.variables.firstname
```
This reference looks for results named `my-name`. The keyword `variables` indicates the value is the `firstname` variable.

Within csvpaths, the most common use for references is within the `print()` function. In the print function, if a reference is local, meaning that it refers to the csvpath that contains it, the syntax is shortened by not specifying the csvpath name. It looks like

```
    $.variables.firstname
```


|Returns    | Matches                                   | Examples               |
|-----------|-------------------------------------------|------------------------|
|Calculated | True, if used in an assignment, otherwise calculated. | `@q = $orders.variables.quarter` |


Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/references.md'>more about references here</a>.

