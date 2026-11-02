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
