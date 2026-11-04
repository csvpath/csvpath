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

    #
    # Verhoeff's dihedral group D5: the multiplication table, and the
    # permutation applied by position
    #
    VERHOEFF_D = (
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
        (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
        (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
        (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
        (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
        (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
        (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
        (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
        (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
        (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
    )
    VERHOEFF_P = (
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
        (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
        (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
        (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
        (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
        (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
        (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
        (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
    )

    @classmethod
    def verhoeff(cls, *, digits: str) -> bool:
        """True if a string of ASCII digits, its last digit the check
        digit, passes the Verhoeff check, as India's Aadhaar numbers do"""
        if not isinstance(digits, str):
            raise TypeError(f"digits must be a str, not {type(digits)}")
        if len(digits) < 2 or not (digits.isascii() and digits.isdigit()):
            raise ValueError(f"digits must be two or more ASCII digits, not {digits!r}")
        c = 0
        for i, ch in enumerate(reversed(digits)):
            c = cls.VERHOEFF_D[c][cls.VERHOEFF_P[i % 8][int(ch)]]
        return c == 0

    ES_ID_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
    ES_NIE_LEADS = {"X": "0", "Y": "1", "Z": "2"}

    @classmethod
    def es_id_letter(cls, *, number: str) -> str:
        """the control letter of a Spanish DNI (8 digits) or NIE (X, Y or
        Z and 7 digits): the number mod 23 indexes TRWAGMYFPDXBNJZSQVHLCKE.
        For a NIE, X, Y and Z count as 0, 1 and 2."""
        if not isinstance(number, str):
            raise TypeError(f"number must be a str, not {type(number)}")
        text = number.upper()
        if len(text) == 8 and text[0] in cls.ES_NIE_LEADS:
            text = cls.ES_NIE_LEADS[text[0]] + text[1:]
        if len(text) != 8 or not (text.isascii() and text.isdigit()):
            raise ValueError(
                f"number must be 8 digits, or X, Y or Z and 7 digits, not {number!r}"
            )
        return cls.ES_ID_LETTERS[int(text) % 23]

    @classmethod
    def fr_nir_key(cls, *, nir: str) -> bool:
        """True if a French NIR (INSEE number), 15 characters without
        separators, has the right key: the last two digits are 97 minus
        the first 13 mod 97. Corsica's departments 2A and 2B count as 19
        and 18."""
        if not isinstance(nir, str):
            raise TypeError(f"nir must be a str, not {type(nir)}")
        text = nir.upper()
        department = text[5:7]
        if department == "2A":
            text = text[:5] + "19" + text[7:]
        elif department == "2B":
            text = text[:5] + "18" + text[7:]
        if len(text) != 15 or not (text.isascii() and text.isdigit()):
            raise ValueError(
                f"nir must be 15 digits, or 2A or 2B in the department, not {nir!r}"
            )
        return 97 - int(text[:13]) % 97 == int(text[13:])

    #
    # RENAPO's CURP alphabet: N is followed by Ñ, so O to Z are worth one
    # more than counting from A = 10
    #
    MX_CURP_ALPHABET = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"

    @classmethod
    def mx_curp_check(cls, *, curp: str) -> str:
        """the check digit of a Mexican CURP, from its first 17
        characters: each character's value in the CURP alphabet times 18
        minus its position (0-based), summed; 10 minus the sum mod 10, with
        10 as 0"""
        if not isinstance(curp, str):
            raise TypeError(f"curp must be a str, not {type(curp)}")
        text = curp.upper()
        if len(text) != 17 or any(c not in cls.MX_CURP_ALPHABET for c in text):
            raise ValueError(f"curp must be 17 letters and digits, not {curp!r}")
        total = sum(
            cls.MX_CURP_ALPHABET.index(c) * (18 - i) for i, c in enumerate(text)
        )
        return str((10 - total % 10) % 10)

    #
    # the Codice Fiscale check: characters in odd positions (1st, 3rd ...)
    # are worth these values, digits 0-9 the same as letters A-J; in even
    # positions a digit is its value and a letter A = 0 ... Z = 25
    #
    IT_CF_ODD = (
        1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18,
        20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23,
    )  # fmt: skip

    @classmethod
    def it_cf_check(cls, *, code: str) -> str:
        """the check letter of an Italian Codice Fiscale, from its first 15
        characters: the odd and even position values, summed, mod 26 as a
        letter"""
        if not isinstance(code, str):
            raise TypeError(f"code must be a str, not {type(code)}")
        text = code.upper()
        if len(text) != 15 or not (text.isascii() and text.isalnum()):
            raise ValueError(f"code must be 15 letters and digits, not {code!r}")
        total = 0
        for i, c in enumerate(text):
            v = int(c) if c.isdigit() else ord(c) - ord("A")
            total += cls.IT_CF_ODD[v] if i % 2 == 0 else v
        return chr(ord("A") + total % 26)

    @classmethod
    def de_idnr(cls, *, digits: str) -> bool:
        """True if 11 ASCII digits are a valid German Steuer-IdNr: no
        leading 0; in the first ten, exactly one digit occurs two or three
        times and the others once; and the ISO 7064 MOD 11,10 check digit"""
        cls._digits(digits=digits, length=11)
        if digits[0] == "0":
            return False
        counts = [digits[:10].count(d) for d in set(digits[:10])]
        repeated = [c for c in counts if c > 1]
        if len(repeated) != 1 or repeated[0] not in (2, 3):
            return False
        #
        # MOD 11,10: carry a product through the digits; the check digit
        # makes the last step land on 1
        #
        product = 10
        for c in digits[:10]:
            total = (int(c) + product) % 10 or 10
            product = (total * 2) % 11
        return (11 - product) % 10 == int(digits[10])

    @classmethod
    def ar_cuit(cls, *, digits: str) -> bool:
        """True if 11 ASCII digits pass the Argentina CUIT/CUIL mod 11
        check: the first ten weighted 5 4 3 2 7 6 5 4 3 2; 11 minus the
        sum mod 11 is the check digit, with 11 as 0 and 10 as 9"""
        cls._digits(digits=digits, length=11)
        total = sum(int(c) * w for c, w in zip(digits, (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)))
        check = 11 - total % 11
        if check == 11:
            check = 0
        elif check == 10:
            check = 9
        return check == int(digits[10])

    @classmethod
    def au_tfn(cls, *, digits: str) -> bool:
        """True if 9 ASCII digits are a valid Australian TFN: weighted 1 4
        3 7 5 8 6 9 10, the sum is divisible by 11"""
        cls._digits(digits=digits, length=9)
        weights = (1, 4, 3, 7, 5, 8, 6, 9, 10)
        return sum(int(c) * w for c, w in zip(digits, weights)) % 11 == 0

    @classmethod
    def gb_utr(cls, *, digits: str) -> bool:
        """True if 10 ASCII digits are a valid UK UTR: the FIRST digit
        checks the other nine, weighted 6 7 8 9 10 5 4 3 2, as
        21987654321 indexed by the sum mod 11"""
        cls._digits(digits=digits, length=10)
        weights = (6, 7, 8, 9, 10, 5, 4, 3, 2)
        total = sum(int(c) * w for c, w in zip(digits[1:], weights))
        return "21987654321"[total % 11] == digits[0]

    ES_CIF_TYPES = "ABCDEFGHJNPQRSUVW"
    ES_CIF_LETTERS = "JABCDEFGHI"

    @classmethod
    def es_cif(cls, *, cif: str) -> bool:
        """True if a Spanish CIF, 9 characters without separators, is
        valid: an organization type letter, 7 digits, and a control
        character from the Luhn check digit of the 7 digits, either the
        digit or JABCDEFGHI indexed by it (sources disagree on which types
        use which, so either is accepted)"""
        if not isinstance(cif, str):
            raise TypeError(f"cif must be a str, not {type(cif)}")
        text = cif.upper()
        if (
            len(text) != 9
            or text[0] not in cls.ES_CIF_TYPES
            or not (text[1:8].isascii() and text[1:8].isdigit())
        ):
            raise ValueError(
                f"cif must be a type letter, 7 digits and a control, not {cif!r}"
            )
        body = text[1:8]
        for d in "0123456789":
            if cls.luhn(digits=body + d):
                return text[8] in (d, cls.ES_CIF_LETTERS[int(d)])
        return False

    @classmethod
    def co_nit(cls, *, digits: str) -> bool:
        """True if ASCII digits, the last the check digit, pass the
        Colombia NIT check: from the right of the body, weighted 3 7 13 17
        19 23 29 37 41 43 47 53 59 67 71, the sum mod 11 indexes
        01987654321"""
        if not isinstance(digits, str):
            raise TypeError(f"digits must be a str, not {type(digits)}")
        if not 2 <= len(digits) <= 16 or not (digits.isascii() and digits.isdigit()):
            raise ValueError(f"digits must be 2 to 16 ASCII digits, not {digits!r}")
        weights = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)
        total = sum(w * int(c) for w, c in zip(weights, reversed(digits[:-1])))
        return "01987654321"[total % 11] == digits[-1]

    @classmethod
    def fr_spi(cls, *, digits: str) -> bool:
        """True if 13 ASCII digits are a valid French tax number (SPI): the
        first digit 0 to 3, and the last three the first ten mod 511"""
        cls._digits(digits=digits, length=13)
        return digits[0] in "0123" and int(digits[:10]) % 511 == int(digits[10:])

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
        "verhoeff": "verhoeff",
        "de_idnr": "de_idnr",
        "ar_cuit": "ar_cuit",
        "au_tfn": "au_tfn",
        "gb_utr": "gb_utr",
        "fr_spi": "fr_spi",
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
