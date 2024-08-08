
# How to create a function

Function classes have two implementation overridden methods:

- `to_value(self, skip=[])` - produces the value of the function
- `matches(self, skip=[])` - determines if the function contributes to a row matching the csvpath

Both methods may be called multiple times per row due to checking qualifier constraints, principly `onmatch`, or for other reasons. When a function checks to see if the other csvpath components all match it passes itself in the skip list. The skip list is a list of match components that should not perform their usual calculations if they find themselves in the list. If your function finds itself in the skip list it should return:

- `self.value` for `to_value`
- `True` for `matches` - this makes sure your function isn't asking itself if it matches

Usually you want to cache the result of calculating `to_value` and `matches`. Two variables are provided for caching:

- self.value
- self.match

A very simple function might look like:

    class MyFunction(Function):
        def to_value(self, skip=[]):
            if self in skip:
                return self.value
            if self.value is None:
                #
                self.calculate_stuff()
                #
            return self.value

        def matches(self, skip=[]):
            if self in skip:
                return True
            if self.match is None:
                #
                self.calculate_stuff()
                #
            return self.match


