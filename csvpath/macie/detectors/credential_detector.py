import base64
import binascii
import hashlib
import json
import re

from ..macie_exceptions import MacieException


class CredentialDetector:
    """finds credentials in a cell, our stand-in for Macie's credentials
    identifiers. Macie publishes the keywords (for AWS and Google Cloud
    keys only), a few exclusions and, for some, the standard the format
    follows. The forms, which the catalog detector's data names:

        aws_secret    AWS_CREDENTIALS: a secret access key, 40 characters
                      of A-Z a-z 0-9 / +, not touching others, and not
                      one part of a dotted token such as a JWT. Ours: one
                      that is all lower case hex (a SHA-1 hash, say) is not
                      a key
        gcp_api_key   GCP_API_KEY: the key string, AIza and 35 characters
                      of A-Z a-z 0-9 _ -
        http_basic    HTTP_BASIC_AUTH_HEADER: a complete header, the field
                      name, the Basic scheme and the credentials (RFC 7617):
                      Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==.
                      The field and scheme in any case; the token is not
                      decoded (ours)
        jwt           JSON_WEB_TOKEN: a JWS compact token (RFC 7519): three
                      base64url parts, the header a JSON object with alg,
                      the payload a JSON object; the signature may be
                      empty, for an unsigned token
        openssh       OPENSSH_PRIVATE_KEY: a whole BEGIN ... END OPENSSH
                      PRIVATE KEY block
        pgp           PGP_PRIVATE_KEY: a whole BEGIN ... END PGP PRIVATE
                      KEY BLOCK block
        pkcs          PKCS: a whole PRIVATE KEY, ENCRYPTED PRIVATE KEY or
                      RSA PRIVATE KEY block; ours, also EC and DSA PRIVATE
                      KEY blocks
        putty         PUTTY_PRIVATE_KEY: Macie's six headers in Macie's
                      order, PuTTY-User-Key-File, Encryption, Comment,
                      Public-Lines, Private-Lines, Private-MAC, with the
                      characters Macie says each value may hold
        stripe        STRIPE_CREDENTIALS: sk_, pk_ or rk_, live_ or test_,
                      and at least 24 letters and digits

    exclusions_sha256, in the catalog data, are never reported: the
    SHA-256 hashes, in hex, of Macie's fictitious examples. They are kept
    as hashes because a credential scanner (GitHub push protection)
    rejects a repo that holds even a published example key. A key block must be whole in one cell; CSV cells
    can hold newlines."""

    B64 = r"[A-Za-z0-9+/]"
    PEM_BODY = r"[A-Za-z0-9+/=\s]+?"
    FORMS = {
        "aws_secret": re.compile(
            #
            # not one part of a dotted token, such as a JWT, whose 40
            # character header would otherwise look like a key
            #
            r"(?<![A-Za-z0-9/+=])(?<![A-Za-z0-9_-]\.)"
            r"[A-Za-z0-9/+]{40}"
            r"(?![A-Za-z0-9/+=])(?!\.[A-Za-z0-9_-])"
        ),
        "gcp_api_key": re.compile(
            r"(?<![A-Za-z0-9_-])AIza[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"
        ),
        "http_basic": re.compile(
            r"(?<![A-Za-z-])(?:Proxy-)?Authorization:[ \t]*Basic[ \t]+[A-Za-z0-9+/]+=*(?![A-Za-z0-9+/=])",
            re.IGNORECASE,
        ),
        "jwt": re.compile(
            r"(?<![A-Za-z0-9_.-])"
            r"(?P<header>[A-Za-z0-9_-]{4,})\.(?P<payload>[A-Za-z0-9_-]{4,})\.(?P<signature>[A-Za-z0-9_-]*)"
            r"(?![A-Za-z0-9_.-])"
        ),
        "openssh": re.compile(
            rf"-----BEGIN OPENSSH PRIVATE KEY-----\s+{PEM_BODY}\s*-----END OPENSSH PRIVATE KEY-----"
        ),
        "pgp": re.compile(
            r"-----BEGIN PGP PRIVATE KEY BLOCK-----.+?-----END PGP PRIVATE KEY BLOCK-----",
            re.DOTALL,
        ),
        "pkcs": re.compile(
            r"-----BEGIN (?P<kind>(?:ENCRYPTED |RSA |EC |DSA )?PRIVATE KEY)-----"
            r"[A-Za-z0-9+/=:,\-\s]+?"
            r"-----END (?P=kind)-----"
        ),
        "putty": re.compile(
            r"PuTTY-User-Key-File-\d+:[ \t]*[A-Za-z0-9-]+\r?\n"
            r"Encryption:[ \t]*[A-Za-z0-9-]+\r?\n"
            r"Comment:[ \t]*[A-Za-z0-9-]+\r?\n"
            r"Public-Lines:[ \t]*\d+\r?\n(?:[A-Za-z0-9/+=-]+\r?\n)+"
            r"Private-Lines:[ \t]*\d+\r?\n(?:[A-Za-z0-9/+=-]+\r?\n)+"
            r"Private-MAC:[ \t]*[A-Za-z0-9+-]+"
        ),
        "stripe": re.compile(
            r"(?<![A-Za-z0-9_])(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{24,}(?![A-Za-z0-9_])"
        ),
    }
    HEX = re.compile(r"[0-9a-f]+")
    SHA256 = re.compile(r"[0-9a-f]{64}")

    #
    # the catalog data keys this detector reads; a project rulesbase may
    # override these and no others
    #
    CONFIG_KEYS = ("form", "exclusions_sha256")

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        self.form = config.get("form")
        if self.form not in self.FORMS:
            raise MacieException(
                f"form must be one of {sorted(self.FORMS)}, not {self.form!r}"
            )
        exclusions = config.get("exclusions_sha256") or []
        if not isinstance(exclusions, list) or not all(
            isinstance(e, str) and self.SHA256.fullmatch(e) for e in exclusions
        ):
            raise MacieException(
                "exclusions_sha256 must be a list of lower case hex SHA-256 hashes"
            )
        self.exclusions = frozenset(exclusions)
        self.candidates = self.FORMS[self.form]

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.candidates.finditer(cell):
            if self.exclusions and self.sha256(text=m.group(0)) in self.exclusions:
                continue
            if self.form == "aws_secret" and self.HEX.fullmatch(m.group(0)):
                continue
            if self.form == "jwt" and not self.is_jwt(match=m):
                continue
            found.append((m.start(), m.end()))
        return found

    @classmethod
    def sha256(cls, *, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def is_jwt(self, *, match: re.Match) -> bool:
        header = self._json(part=match.group("header"))
        payload = self._json(part=match.group("payload"))
        return (
            isinstance(header, dict) and "alg" in header and isinstance(payload, dict)
        )

    @classmethod
    def _json(cls, *, part: str):
        #
        # base64url without padding, as JWS uses
        #
        try:
            text = base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))
            return json.loads(text.decode("utf-8"))
        except (binascii.Error, ValueError, UnicodeDecodeError):
            return None
