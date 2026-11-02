class ChecksumUtility:
    """check-digit algorithms the managed identifier detectors share"""

    @classmethod
    def luhn(cls, *, digits: str) -> bool:
        """True if a string of ASCII digits passes the Luhn (mod 10) check"""
        if not isinstance(digits, str):
            raise TypeError(f"digits must be a str, not {type(digits)}")
        if digits == "" or not (digits.isascii() and digits.isdigit()):
            raise ValueError(f"digits must be one or more ASCII digits, not {digits!r}")
        total = 0
        #
        # from the right, double every second digit; a doubled digit over 9
        # contributes its two digits, i.e. minus 9
        #
        for i, c in enumerate(reversed(digits)):
            d = int(c)
            if i % 2 == 1:
                d = d * 2
                if d > 9:
                    d = d - 9
            total += d
        return total % 10 == 0

    @classmethod
    def nhs_mod11(cls, *, digits: str) -> bool:
        """True if 10 ASCII digits pass the UK NHS number check: weight the
        first nine digits 10 down to 2, and 11 minus the sum's remainder
        mod 11 (11 becomes 0) must equal the tenth digit. A result of 10
        means the number is never issued."""
        if not isinstance(digits, str):
            raise TypeError(f"digits must be a str, not {type(digits)}")
        if len(digits) != 10 or not (digits.isascii() and digits.isdigit()):
            raise ValueError(f"digits must be 10 ASCII digits, not {digits!r}")
        total = sum(int(c) * w for c, w in zip(digits[:9], range(10, 1, -1)))
        check = 11 - total % 11
        if check == 11:
            check = 0
        return check != 10 and check == int(digits[9])

    CHECKS = {"luhn": "luhn", "nhs_mod11": "nhs_mod11"}

    @classmethod
    def check(cls, *, name: str, digits: str) -> bool:
        """runs a digit check by its catalog name"""
        if name not in cls.CHECKS:
            raise ValueError(f"No digit check named {name!r}")
        return getattr(cls, cls.CHECKS[name])(digits=digits)

    @classmethod
    def iban_mod97(cls, *, iban: str) -> bool:
        """True if an IBAN, without separators, passes the ISO 7064
        MOD 97-10 check of ISO 13616: move the first four characters to
        the end, replace each letter with two digits (A=10 ... Z=35), and
        the number must leave a remainder of 1 when divided by 97"""
        if not isinstance(iban, str):
            raise TypeError(f"iban must be a str, not {type(iban)}")
        text = iban.upper()
        if len(text) < 5 or not (text.isascii() and text.isalnum()):
            raise ValueError(
                f"iban must be at least five ASCII letters and digits, not {iban!r}"
            )
        rearranged = text[4:] + text[:4]
        digits = "".join(
            c if c.isdigit() else f"{ord(c) - ord('A') + 10}" for c in rearranged
        )
        return int(digits) % 97 == 1
