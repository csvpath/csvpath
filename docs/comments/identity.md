
<a name="identity"></a>
# A Csvpath's Identity

Every csvpath has an identity. Its identity is used to point to it in references, error messages, and other places where knowing which csvpath was active is important.

By default a csvpath's identity is added to the metadata as `NAME:0`, where `0` is the zero-based position of the csvpath in a set of csvpaths, referred to as a named-paths group. A csvpath writer can and should override this generic index identity with a more meaningful name. They do this by setting the identity using a special metadata field.

The identity field is set in an outer comment. It is the word `ID` or `NAME`. Variations of those names are acceptable:
* ALL CAPS, the default
* Initial caps
* All lowercase

If `name` and `id` are both set, `id` takes precedence. The default index is always added as `NAME`, the lowest precedence identity field name, typically resulting in you having both your meaningful identity and the index in metadata.

## Error Messages

The most immediately important use of a csvpath's identity is typically in error messages. If your `config.ini` is set to use the default error pattern, or any error pattern that includes `{instance}`, you will see the identity of a csvpath in error messages. Within CsvPath Framework, the terms "identity" and "instance" are used interchangeably.

For example, the default verbose error pattern is:
```
    {time}:{file}:{line}:{paths}:{instance}:{chain}:  {message}
```

If there is an error with a csvpath that has the identity `example one` it might look like:
```
    2025-10-31 17h24m16s-718972:people.csv:2::example one:person:  Invalid value at person.id
```

There is more information about error patterns and error handling configuration on [csvpath.org](https://www.csvpath.org).

