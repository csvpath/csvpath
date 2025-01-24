
# Email and Url

`email()` tests a header value, or the value of a function, variable, or reference, to see if it is a standard-form email address.

The argument to `email()` is either a quoted header name that dereferences to the header's value, or it is a function, variable, or reference. You cannot test a term as an email because as the csvpath writer you can validate for yourself if you are typing in an email.

As with the other types, unless the `notnone` qualifier is present, `none()` or `None` are accepted values, despite not being emails.

### `url()`

`url()` is similar to `email()` but identifies standard URLs. The URL function does not return `True` for non-standard URLs such as `s3://...` and `jdbc:...`. For those you must use `regex()`.

## Examples

```bash
    $[1*][
        email("address")
    ]
```

This csvpath checks if the value in #address is an email.

```bash
    $[1*][
        email(#address)
    ]
```

Likewise, this csvpath checks the value of #address. If it is not, a validation error message will be printed or a validation exception will be thrown, assuming `validation-mode` has `raise` and/or `print`.

```bash
    $[1*][
        @email_ok = email(@address)
    ]
```

As you would guess, @address is checked to see if it is an email.



