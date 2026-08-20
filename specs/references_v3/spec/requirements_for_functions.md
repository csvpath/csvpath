# Requirements For Reference Functions



## Hard requirements

### Form is colon name parentheses with or without an arg

### Function arg can be a function, value, or variable

### A function is looked up and validated at runtime

### There is no overlap or code-sharing between CsvPath Validation Language
    and CsvPath Reference Language.



## Strongly held opinions that could change

### Functions must be self validating

### Functions can have no more than 1 arg

### Functions must be self describing and programmatically inspectable.
    Self-description supports both human-readable and machine-actionable
    needs.

### Reference Language should support type-ahead, so functions must be
    prepared to contribute to that capability.

### Functions must self-report whether they are a context setter, a
    pointer, or a value function (see below for the third role).

    A context setter narrows the current scope without resolving to a
    specific item (e.g. :before()/:after()/:from()/:to()). Note that
    :yesterday() and :quarter() are NOT context setters themselves --
    see the value function entry below; they are what a context setter
    like :before() takes as its boundary argument.
    A pointer resolves the current scope down to exactly 0 or 1 item
    (e.g. :last(), :first(), :index(5), :uuid("...")). A bare name_one
    made up only of functions is implicitly scoped by "*" -- name_one ==
    :first() means the same as *:first().

    What a pointer resolves to depends on where it sits. In name_one a
    pointer resolves to a physical file, a named-paths group version, or
    a run (a set of results). In name_three a pointer resolves to a well
    known file (e.g. :errors()) -- unless that pointer itself takes
    another pointer as its argument, in which case it resolves to a
    specific value inside that file instead (e.g.
    :errors(:idchain("add[0]string[2]"))). There is no separate "value
    extractor" trait for this -- it is the same pointer trait, just
    nested one level deeper.

### At most one pointer is allowed per function chain, at any one
    nesting level.

    A pointer used as another function's argument resolves that
    function's own internal scope -- it does not act as, and does not
    count as, the pointer for the function chain it is nested within.
    So :errors(:idchain("...")) is fine (one pointer, idchain, at the
    argument level; one pointer, errors, at the top level of its
    chain), but two pointers side by side in the same chain (e.g.
    :last():index(3)) is not.

### Functions within the same chain (the same nesting level) are
    commutative -- lexical order does not matter.

    All functions in a chain are ANDed together (see "Functions and
    Wildcards" above); AND is commutative, so a chain's context
    setters can be written in any order and mean the same thing, and
    the chain's one legal pointer applies to whatever survives that
    AND regardless of where it sits lexically. So
    :before(:yesterday()):index(3) and :index(3):before(:yesterday())
    are the same reference.

### A third role exists alongside context setter and pointer: a value
    function.

    Context setters and pointers both operate on the current scope --
    narrowing it, or reducing it to one item. A value function does
    neither. It computes a value (usually clock/calendar-derived, e.g.
    :year(), :quarter(), :today(), :yesterday(), :hour(), :hours(-24),
    or a bare :date("...")) and behaves like a computed literal
    wherever it is used: as a path segment (matched/narrowed by
    equality, exactly as a literal string would be), or as an argument
    feeding a true context setter's boundary (e.g.
    :before(:yesterday()) -- :yesterday() supplies the value,
    :before() is the context setter that narrows scope with it).

    A value function never counts toward the "at most one pointer per
    chain" rule, and needs no special handling for the bare-"*"-
    must-be-qualified rule either -- once it resolves to a value it is
    exactly as "complete" as a literal segment.

### String args support "{...}" interpolation, as the substitute for a
    multi-arg :concat()

    Because a function takes at most 1 arg (see above), there is no way
    to write :concat(). Instead, a quoted string arg may contain one or
    more "{...}" spans: a bare @variable (:name("partner-{@company}-
    orders")) or a call to a value-role function (:name("partner-
    {:year()}-orders")). Multiple spans in one string are fine
    (:name("partner-{:year()}-{@company}")). Only a value function is
    legal inside "{...}" -- a context setter or pointer is not, since
    neither produces a plain value to splice in. "{{" / "}}" escapes a
    literal brace, matching the convention already used elsewhere in
    the codebase (csvpath/util/var_utility.py's substitute()).

    Implementation note: parsing/validation of this shape is built
    (InterpolatedString3 in reference_3.py); actually resolving one into
    its final text is deferred until a runtime CsvPaths/variable context
    and a real value function exist -- see references_v3_compendium.md.

### Functions only "see" each other if they are nested

### Functions cannot be explicitly compared
    i.e. there is nothing like $*.results.*.*:errors():index() == 5. Instead
    we might do $*.results.*.*:errors(:index(5))

### The csvpath.matching.functions.FunctionFactory is a reasonable rough
    draft for the implementation of the Reference Language functions factory.



## Possible requirements or limitations

### Custom functions can be created by end users (tho perhaps not intended for customer users)

### No CsvPath Validation Language qualifier-like syntax is required in CsvPath Reference Langauge



