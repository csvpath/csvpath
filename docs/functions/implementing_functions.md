
# How to create a function

You can easily create your own function, register it for use, and use it in your csvpaths.

Functions are descendants of the Function class. Most of the built-ins extend one of:
- ValueProducer - for functions that mainly generate information
- MatchDecider - for functions that mainly do a true/false response to information
- SideEffect - for functions that don't add or consider information in the current line, but rather have some side effect such as printing, setting validity, advancing lines, etc.

These three classes are only indicators. You can extend Function directly.

    from csvpath.matching.functions.function import Function
    class MyFunction(Function):
        ...

Function implementations override three methods:

- `_produce_value(self, skip=[])` - produces the value of the function
- `_decide_match(self, skip=[])` - determines if the function contributes to a row matching the csvpath
- `check_valid(self)` - raises an exception if the function is configured incorrectly

The first two methods may be called multiple times per row due to checking qualifier constraints, principally `onmatch`, or for other reasons. When a function checks to see if the other csvpath components all match it passes itself in the skip list. The skip list is a list of match components that should not perform their usual calculations if they find themselves in the list. If your function finds itself in the skip list it should immediately return. The return value should be:

- `self.value` for `_produce_value`
- `self.default_match()` for `matches`

Usually you want to cache the result of calculating `to_value` and `matches`. Two variables are provided for caching. It is important to set them to a non-None value in order to prevent your function running multiple times.

- self.value
- self.match

## Qualifiers

Qualifiers are available to your function. They are accessed using the methods in the Qualified class. Qualified is an ancestor of Function. The most relevant capabilities are:

- first_non_term_qualifier()
- qualifiers

The former will get you a non-built-in qualifier. The `qualifiers` property gives you access to all qualifiers.

All match components support the `onmatch` qualifier. All components support the `nocontrib` when they are on the left-hand side of a when/do (`->`) operation.

## Arguments Validation

Validation is an important step that happens before any rows are considered. It allows for structural csvpath problems to be discovered before you start processing files. The validity checks only address the number of children and the type of children. You cannot check types or values ofdata provided by child match components because the match components are not setup yet and there is no data at the time validation happens.

The most common validations are methods available on the `Validation` class. `Validation` is an ancestor class of Function.


## Example

A very simple function might look like:

```python
    class MyFunction(Function):
        def _produce_value(self, skip=[]) -> None:
            v = self.calculate_stuff()
            self.value = v

        def _decide_match(self, skip=[]) -> None:
            m = self.calculate_stuff()
            self.match = result

        def check_valid(self) -> None:
            self.validate_zero_args()
            # you must call check_valid so that your
            # function's children are validated.
            super().check_valid()
```

When your function's match depends on its value, or its value depends on its match, it needs to call the appropriate method:
- To get the value, call self.to_value(skip=skip)
- To check the match, call self.matches(skip=skip)

When your function needs its arguments you can call:
- self._child_one()
- self._value_one(skip=skip)
- self._child_two()
- self._value_two(skip=skip)
- self._siblings()

When you need to get a value or a match from a child object you use `to_value()` or `matches()`. Remember to pass the skip list as the named argument `skip`.

## Registering

To register your function for use, add it to the `FunctionFactory` like this:

```python
    from csvpath.matching.functions.function_factory import FunctionFactory
    FunctionFactory.add_function(name='iamafunction', function=my_function_instance)
```

Alternatively, add a file path to your `config.ini` file under the key `[functions][imports]` that points to a list of functions to register. The key is like:

    [functions]
    imports = my_imports/functions.txt

In the file list every function on its own line using a format like that of Python imports:

    from a.b.c.my_function import MyFunction as iamafunction

To use your function do something like:

```bash
    "$test[*][ @t = iamafunction() ]"
```

Behind the scenes an instance of your function will be retrieved with:

```python
    f = FunctionFactory.get_function(matcher=None, name="iamafunction")
```

The name you set on FunctionFactory must match the name passed in when a function is requested.

