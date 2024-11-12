
# Fingerprinting

The fingerprint functions take a sha256 digest of your file or lines for future reference. These functions are critical to the long-term identification of files, finding duplicates, and ascertaining a file has not changed.

Use `line_fingerprint()` to create a line by line hash as you iterate through a delimited file. At the end of the iteration, use `last()` and `store_fingerprint()` to create a hex digest in the `CsvPath` instance's `metadata` property. If you use a `CsvPaths` instance to drive your `CsvPath` instances your metadata, including the hash, will be stored with your csvpath's results in the archive directory.

To simply get a sha256 digest of the entire file in one go, use the `file_fingerprint()` function. The fingerprint will end up in the `metadata`.

The fingerprint functions can take an arbitrary name qualifier to name their metadata keys and intermediate variables. If you do not provide your own variable names you will see:
- `line_fingerprint()` values in a `by_line_fingerprint`
- `file_fingerprint()` in a `fingerprint`

If you give `line_fingerprint()` a name you must use the same name on `store_fingerprint()`.

The metadata will also receive a `hash_algorithm` key with the value `sha256`

## Examples

```bash
    $[*][
        firstline() -> file_fingerprint()
        line_fingerprint.lineshash()
        last() -> store_fingerprint.lineshash()
    ]
```

This csvpath will result in the CsvPath instance's metadata looking like this:

```json
    { "fingerprint":"6541e28c6330b910e47f1ef406259c17690612630936ce5784522cf05afadffa",
      "lineshash":"c299f3f275efc3999d733af13d02dfb2aaef2b707616443160a24c0f96f026b3",
      "hash_algorithm":"sha256"
    }
```

If you are using a `CsvPaths` instance the same metadata will be in the `meta.json` file in your results directory in the archive.

