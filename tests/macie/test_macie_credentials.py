"""Credentials stand-ins: CredentialDetector's forms and the catalog
entries. Credential-shaped test values (key blocks, Stripe and Google
keys) are built at run time from parts, so that no file in the repo looks
like a leaked secret to a secret scanner. None of them is real."""

import base64
import json

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.credential_detector import CredentialDetector
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
#
# 40 characters, fake, and not all hex
#
AWS = "FAKEfakeFAKEfake/TESTtestTEST+fake123456"
BEGIN = "-----" + "BEGIN "
END = "-----" + "END "


def _block(
    kind: str,
    body: str = "MIIBOgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKLs1Pt8Qu",
) -> str:
    return f"{BEGIN}{kind}-----\n{body}\n{body[::-1]}\n{END}{kind}-----"


def _b64url(obj) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")


JWT = f"{_b64url({'alg': 'HS256', 'typ': 'JWT'})}.{_b64url({'sub': '1234567890'})}.c2lnbmF0dXJl"
UNSIGNED_JWT = f"{_b64url({'alg': 'none'})}.{_b64url({'sub': 'x'})}."
GCP = "AI" + "za" + "SyFAKEfakeFAKEfake0123456789-_abcde"
STRIPE_LIVE = "sk_" + "live_" + "FAKEfakeFAKEfake01234567"
#
# Stripe's published code examples, which Macie never reports, built from
# parts for the same reason the catalog holds only their hashes
#
STRIPE_SK_EXAMPLE = "sk_" + "test_" + "4eC39HqLyjWDarjtT1zdp7dc"
STRIPE_PK_EXAMPLE = "pk_" + "test_" + "TYooMQauvdEDq54NiTphI7jx"
PUTTY = (
    "PuTTY-User-Key-File-2: ssh-rsa\n"
    "Encryption: none\n"
    "Comment: rsa-key-20261103\n"
    "Public-Lines: 2\n"
    "AAAAB3NzaC1yc2EAAAABJQAAAQEAhFAKE\n"
    "fakeFAKE/fake+FAKE=\n"
    "Private-Lines: 1\n"
    "AAABAQCFAKEfake\n"
    "Private-MAC: 5f2a+b1c"
)


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, name: str) -> CredentialDetector:
    return CredentialDetector(config=catalog.detector(name=name))


def _mdi(catalog, name: str) -> ManagedIdentifier:
    e = catalog.identifier(name=name)
    return ManagedIdentifier(
        name=name,
        category=e["category"],
        detector=e["detector"],
        keyword_mode=e["keyword_mode"],
        keywords=e["keywords"],
        distance=e["distance"],
        severity=SeverityLevels.parse(text=e["severity"]),
        catalog=catalog,
    )


def test_macie_credentials_fixtures() -> None:
    assert len(AWS) == 40
    assert len(GCP) == 39


# =============
# each form
# =============


@pytest.mark.parametrize(
    "name, cell",
    [
        ("aws_secret", AWS),
        ("gcp_api_key", GCP),
        ("http_basic", "Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="),
        ("http_basic", "Proxy-Authorization: Basic dGVzdDoxMjPCow=="),
        ("http_basic", "authorization:basic dGVzdDoxMjM="),
        ("jwt", JWT),
        ("jwt", UNSIGNED_JWT),
        ("openssh", _block("OPENSSH PRIVATE KEY")),
        ("pgp", _block("PGP PRIVATE KEY BLOCK", "Version: GnuPG v2\n\nlQOYBFAKE")),
        ("pkcs", _block("PRIVATE KEY")),
        ("pkcs", _block("ENCRYPTED PRIVATE KEY")),
        ("pkcs", _block("RSA PRIVATE KEY")),
        ("pkcs", _block("EC PRIVATE KEY")),
        ("putty", PUTTY),
        ("stripe", STRIPE_LIVE),
        ("stripe", "pk_" + "test_" + "FAKEfakeFAKEfake01234567"),
        ("stripe", "rk_" + "live_" + "FAKEfakeFAKEfake01234567890abcdef"),
    ],
)
def test_macie_credential_forms(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        #
        # Macie's fictitious examples
        #
        ("aws_secret", "je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY"),
        ("aws_secret", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
        ("stripe", STRIPE_SK_EXAMPLE),
        ("stripe", STRIPE_PK_EXAMPLE),
        #
        # ours: 40 lower case hex is a hash; 39 or 41 characters
        #
        ("aws_secret", "da39a3ee5e6b4b0d3255bfef95601890afd80709"),
        ("aws_secret", AWS[:-1]),
        ("aws_secret", AWS + "x"),
        ("gcp_api_key", GCP[:-1]),
        ("gcp_api_key", "AIzb" + GCP[4:]),
        #
        # a header needs its field name and the Basic scheme
        #
        ("http_basic", "Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="),
        ("http_basic", "Authorization: Bearer QWxhZGRpbjpvcGVuIHNlc2FtZQ=="),
        ("http_basic", "X-Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="),
        #
        # three dotted parts that are not JSON; no alg; a version number
        #
        ("jwt", "abcd.efgh.ijkl"),
        ("jwt", f"{_b64url({'typ': 'JWT'})}.{_b64url({'sub': 'x'})}.c2ln"),
        ("jwt", f"{_b64url({'alg': 'HS256'})}.{_b64url(['not', 'an', 'object'])}.c2ln"),
        ("jwt", "1.2.3"),
        #
        # a public key, or half a block
        #
        ("pkcs", _block("PUBLIC KEY")),
        ("pkcs", _block("RSA PRIVATE KEY").split(END)[0]),
        ("openssh", _block("RSA PRIVATE KEY")),
        ("pgp", _block("PGP PUBLIC KEY BLOCK")),
        #
        # Macie: no spaces in header values, no custom headers
        #
        ("putty", PUTTY.replace("rsa-key-20261103", "my key")),
        ("putty", PUTTY.replace("Encryption: none\n", "Encryption: none\nCustom: x\n")),
        ("stripe", "sk_" + "live_" + "short"),
        ("stripe", "sk_" + "prod_" + "FAKEfakeFAKEfake01234567"),
    ],
)
def test_macie_credential_not_detected(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == []


def test_macie_credentials_in_text(catalog) -> None:
    cell = f"curl -H 'Authorization: Basic dGVzdDoxMjM=' {JWT} and more"
    assert _detector(catalog, "http_basic").matches(cell=cell) == [(9, 42)]
    start = cell.index(JWT)
    assert _detector(catalog, "jwt").matches(cell=cell) == [(start, start + len(JWT))]
    two = f"{_block('RSA PRIVATE KEY')}\n\n{_block('PRIVATE KEY')}"
    assert len(_detector(catalog, "pkcs").matches(cell=two)) == 2


def test_macie_aws_secret_is_not_part_of_a_jwt(catalog) -> None:
    #
    # this JWT's header is 40 base64 characters; near an AWS keyword it
    # must still not be an AWS secret key
    #
    token = f"{_b64url({'alg': 'HS256', 'typ': 'JWT'})}.{_b64url({'sub': 'x'})}.c2ln"
    assert len(token.split(".")[0]) == 40
    aws = _mdi(catalog, "AWS_CREDENTIALS")
    assert (
        aws.occurrences(cell=f"credentials {token}", header="x", allow_lists=NO_ALLOW)
        == 0
    )
    #
    # a key at the end of a sentence is still a key
    #
    assert (
        aws.occurrences(
            cell=f"the secret key is {AWS}.", header="x", allow_lists=NO_ALLOW
        )
        == 1
    )


def test_macie_credential_exclusions_are_hashes(catalog) -> None:
    #
    # the catalog holds no example key in clear, only hashes that match
    #
    for name, examples in [
        ("stripe", [STRIPE_SK_EXAMPLE, STRIPE_PK_EXAMPLE]),
        (
            "aws_secret",
            [
                "je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY",
                "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            ],
        ),
    ]:
        data = catalog.detector(name=name)
        assert "exclusions" not in data
        assert data["exclusions_sha256"] == [
            CredentialDetector.sha256(text=e) for e in examples
        ]


def test_macie_credential_bad_config() -> None:
    with pytest.raises(TypeError):
        CredentialDetector(config=None)
    for bad in [
        {},
        {"form": "password"},
        {"form": "jwt", "exclusions_sha256": "x"},
        {"form": "jwt", "exclusions_sha256": ["not a hash"]},
        {"form": "jwt", "exclusions_sha256": ["A" * 64]},
    ]:
        with pytest.raises(MacieException):
            CredentialDetector(config=bad)
    with pytest.raises(TypeError):
        CredentialDetector(config={"form": "jwt"}).matches(cell=None)


# =============
# catalog entries and identifiers
# =============

NAMES = [
    "AWS_CREDENTIALS",
    "GCP_API_KEY",
    "HTTP_BASIC_AUTH_HEADER",
    "JSON_WEB_TOKEN",
    "OPENSSH_PRIVATE_KEY",
    "PGP_PRIVATE_KEY",
    "PKCS",
    "PUTTY_PRIVATE_KEY",
    "STRIPE_CREDENTIALS",
]


def test_macie_credentials_catalog(catalog) -> None:
    for n in NAMES:
        e = catalog.identifier(name=n)
        assert e["category"] == "CREDENTIALS"
        assert e["severity"] == "1:HIGH"
        keyed = n in ("AWS_CREDENTIALS", "GCP_API_KEY")
        assert e["keyword_mode"] == ("required" if keyed else "none")
    assert (
        "aws_secret_access_key"
        in catalog.identifier(name="AWS_CREDENTIALS")["keywords"]
    )
    assert "X-goog-api-key" in catalog.identifier(name="GCP_API_KEY")["keywords"]


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("AWS_CREDENTIALS", AWS, "aws_secret_access_key", 1),
        ("AWS_CREDENTIALS", f"secret key: {AWS}", "x", 1),
        ("AWS_CREDENTIALS", AWS, "notes", 0),
        ("GCP_API_KEY", GCP, "google-api-key", 1),
        ("GCP_API_KEY", GCP, "notes", 0),
        #
        # the others need no keyword
        #
        ("HTTP_BASIC_AUTH_HEADER", "Authorization: Basic dGVzdDoxMjM=", "notes", 1),
        ("JSON_WEB_TOKEN", JWT, "notes", 1),
        ("PKCS", _block("PRIVATE KEY"), "notes", 1),
        ("PUTTY_PRIVATE_KEY", PUTTY, "notes", 1),
        ("STRIPE_CREDENTIALS", STRIPE_LIVE, "notes", 1),
    ],
)
def test_macie_credential_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )


def test_macie_credentials_convert() -> None:
    w = MacieWrapperLoader.from_path(
        path="tests/macie/test_resources/wrappers/handcrafted_minimal.macie.json"
    )
    w["selection"]["managedDataIdentifierIds"] = list(NAMES)
    w["managedDataIdentifiers"]["resolved"] = list(NAMES)
    conversion = MacieConverter(wrapper=w).convert(name="t")
    assert conversion.report.skipped == []
    assert conversion.csvpath.count('"CREDENTIALS"') == 9
