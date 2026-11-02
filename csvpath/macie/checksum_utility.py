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

    @classmethod
    def cpf_mod11(cls, *, digits: str) -> bool:
        """True if 11 ASCII digits are a valid Brazil CPF: two mod 11 check
        digits, the first over nine digits weighted 10 down to 2, the
        second over ten weighted 11 down to 2; a result of 10 is 0"""
        cls._digits(digits=digits, length=11)
        for k in (9, 10):
            total = sum(int(digits[i]) * (k + 1 - i) for i in range(k))
            d = (total * 10) % 11
            if d == 10:
                d = 0
            if d != int(digits[k]):
                return False
        return True

    CNPJ_WEIGHTS = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    @classmethod
    def cnpj_mod11(cls, *, digits: str) -> bool:
        """True if 14 ASCII digits are a valid Brazil CNPJ: two mod 11 check
        digits over the first twelve, then thirteen, digits; a remainder
        under 2 gives 0, otherwise 11 minus the remainder"""
        cls._digits(digits=digits, length=14)
        for k, weights in ((12, cls.CNPJ_WEIGHTS), (13, [6] + cls.CNPJ_WEIGHTS)):
            r = sum(int(digits[i]) * weights[i] for i in range(k)) % 11
            d = 0 if r < 2 else 11 - r
            if d != int(digits[k]):
                return False
        return True

    @classmethod
    def rut_check(cls, *, body: str) -> str:
        """the check character of a Chile RUT or RUN body: weights 2 to 7
        repeating from the right, 11 minus the remainder mod 11; 11 is "0"
        and 10 is "K" """
        if not isinstance(body, str):
            raise TypeError(f"body must be a str, not {type(body)}")
        if body == "" or not (body.isascii() and body.isdigit()):
            raise ValueError(f"body must be one or more ASCII digits, not {body!r}")
        total = 0
        weight = 2
        for c in reversed(body):
            total += int(c) * weight
            weight = weight + 1 if weight < 7 else 2
        r = 11 - total % 11
        if r == 11:
            return "0"
        if r == 10:
            return "K"
        return f"{r}"

    #
    # letters in a French account number count as digits for the RIB key
    #
    FR_RIB_LETTERS = {
        **dict.fromkeys("AJ", "1"),
        **dict.fromkeys("BKS", "2"),
        **dict.fromkeys("CLT", "3"),
        **dict.fromkeys("DMU", "4"),
        **dict.fromkeys("ENV", "5"),
        **dict.fromkeys("FOW", "6"),
        **dict.fromkeys("GPX", "7"),
        **dict.fromkeys("HQY", "8"),
        **dict.fromkeys("IRZ", "9"),
    }

    @classmethod
    def fr_rib_key(cls, *, bban: str) -> bool:
        """True if a 23-character French BBAN (bank 5, branch 5, account
        11, key 2) has the right RIB key: 97 minus (89 x bank + 15 x branch
        + 3 x account) mod 97, with the account's letters counted as
        digits"""
        if not isinstance(bban, str):
            raise TypeError(f"bban must be a str, not {type(bban)}")
        text = bban.upper()
        if (
            len(text) != 23
            or not (text[:10].isascii() and text[:10].isdigit())
            or not (text[21:].isascii() and text[21:].isdigit())
            or not (text[10:21].isascii() and text[10:21].isalnum())
        ):
            raise ValueError(f"bban must be a 23-character French BBAN, not {bban!r}")
        account = "".join(cls.FR_RIB_LETTERS.get(c, c) for c in text[10:21])
        total = 89 * int(text[:5]) + 15 * int(text[5:10]) + 3 * int(account)
        return 97 - total % 97 == int(text[21:])

    ES_WEIGHTS = [1, 2, 4, 8, 5, 10, 9, 7, 3, 6]

    @classmethod
    def es_bban(cls, *, bban: str) -> bool:
        """True if a 20-digit Spanish BBAN (bank 4, branch 4, check 2,
        account 10) has the right check digits: the first over 00 + bank +
        branch, the second over the account, each 11 minus the weighted sum
        mod 11, where 11 is 0 and 10 is 1"""
        cls._digits(digits=bban, length=20)

        def digit(part: str) -> int:
            d = 11 - sum(int(c) * w for c, w in zip(part, cls.ES_WEIGHTS)) % 11
            return 0 if d == 11 else 1 if d == 10 else d

        return f"{digit('00' + bban[:8])}{digit(bban[10:])}" == bban[8:10]

    @classmethod
    def _digits(cls, *, digits: str, length: int) -> None:
        if not isinstance(digits, str):
            raise TypeError(f"digits must be a str, not {type(digits)}")
        if len(digits) != length or not (digits.isascii() and digits.isdigit()):
            raise ValueError(f"digits must be {length} ASCII digits, not {digits!r}")

    CHECKS = {
        "luhn": "luhn",
        "nhs_mod11": "nhs_mod11",
        "cpf_mod11": "cpf_mod11",
        "cnpj_mod11": "cnpj_mod11",
    }

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
