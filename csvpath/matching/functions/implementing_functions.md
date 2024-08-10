
# How to create a function

You can easily create your own function, register it for use, and use it in your csvpaths.

Functions extend the Function class using:

    from csvpath.matching.functions.function import Function
    class MyFunction(Function):
        ...

Function classes have two implementation overridden methods:

- `to_value(self, skip=[])` - produces the value of the function
- `matches(self, skip=[])` - determines if the function contributes to a row matching the csvpath

Both methods may be called multiple times per row due to checking qualifier constraints, principly `onmatch`, or for other reasons. When a function checks to see if the other csvpath components all match it passes itself in the skip list. The skip list is a list of match components that should not perform their usual calculations if they find themselves in the list. If your function finds itself in the skip list it should return:

- `self.value` for `to_value`
- `True` for `matches` - this makes sure your function isn't asking itself if it matches

Usually you want to cache the result of calculating `to_value` and `matches`. Two variables are provided for caching:

- self.value
- self.match

Your function must inherit from Function. It may implement `__init__` and take a `Matcher` object and a string name.

A very simple function might look like:

```python
    class MyFunction(Function):
        def to_value(self, skip=[]):
            if self in skip:
                return self._noop_value()

            if self.value is None:
                #
                self.calculate_stuff()
                #
            return self.value

        def matches(self, skip=[]):
            if self in skip:
                return self._noop_match()
            if self.match is None:
                #
                self.calculate_stuff()
                #
            return self.match
```

In the common case the match depends on the value. In some cases, however, the value depends on the match. When the value is dependent and your function finds itself in the skip list return a call to `self.match()`; otherwise, call `self._noop_value()`. In either case when the match finds `self` in the skip list it should return `self._noop_match()`.

To register your function add it to the FunctionFactory like this:

        FunctionFactory.add_function(name='iamafunction', function=my_function_instance)

To use your function do something like:

        "$test[*][ @t = iamafunction() ]"

Behind the scenes an instance of your function will be retrieved with:

        f = FunctionFactory.get_function(matcher=None, name="iamafunction")

The name you set on FunctionFactory must match the name passed in when a function is requested.

