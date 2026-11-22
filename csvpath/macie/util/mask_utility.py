class MaskUtility:
    """masks the values a Jev review is told about, so that no value leaves
    the machine (specs/macie/jev-review-build.md). The notation is
    FormatDetector's: each letter becomes A and each digit #; spaces and
    punctuation are kept, so a value's shape is all that is left."""

    LETTER = "A"
    LOWER = "a"
    DIGIT = "#"

    @classmethod
    def mask(cls, *, text: str) -> str:
        """309-04-7794 -> ###-##-####; RSSMRA85T10A562S -> AAAAAA##A##A###A"""
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        return "".join(
            cls.LETTER if c.isalpha() else cls.DIGIT if c.isdigit() else c for c in text
        )

    @classmethod
    def mask_cell(cls, *, text: str) -> str:
        """masks every space-separated word holding a digit, which is where
        values are, and keeps the other words, which are the context:
        "ssn on file: 721-99-9913" -> "ssn on file: ###-##-####". A value
        with no digit in it, such as a name, is not masked."""
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        return " ".join(
            cls.mask(text=w) if any(c.isdigit() for c in w) else w
            for w in text.split(" ")
        )

    @classmethod
    def mask_case(cls, *, text: str) -> str:
        """the case-keeping mask, for the NAME and ADDRESS check
        (specs/macie/jev-names-addresses-design.md): each upper-case letter
        becomes A, each lower-case letter a, each digit #; spaces and
        punctuation are kept. Every word is masked, so no word is sent:
        "Akua Mansa" -> "Aaaa Aaaaa"; "12 Main St" -> "## Aaaa Aa"
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        return "".join(
            cls.DIGIT
            if c.isdigit()
            else cls.LETTER
            if c.isalpha() and c.isupper()
            else cls.LOWER
            if c.isalpha()
            else c
            for c in text
        )
