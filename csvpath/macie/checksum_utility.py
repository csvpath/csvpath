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
