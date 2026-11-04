"""ChecksumUtility against python-stdnum, an independent implementation of
the same published checks (a dev dependency; not used by the Macie
package itself). Each check runs on seeded random inputs, so a mistake
in a table or a weight, like the mistyped Verhoeff row this caught
before batch 6 shipped, fails here even when the hand-picked examples in
the other tests still pass.

Where our detectors deliberately differ from stdnum (e.g. CURP sex X,
Aadhaar palindromes), the difference is in the detector, not the check,
and these tests compare only the checks."""

import random
import string

import pytest
from stdnum import luhn, verhoeff
from stdnum.br import cnpj, cpf
from stdnum.cl import rut
from stdnum.es import dni, nie
from stdnum.fr import nir
from stdnum.gb import nhs
from stdnum.iso7064 import mod_97_10
from stdnum.it import codicefiscale, iva
from stdnum.mx import curp

from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.it_cf_detector import ItCfDetector

N = 2000
DIGITS = string.digits
UPPER = string.ascii_uppercase


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(DIGITS) for _ in range(n))


def test_macie_oracle_luhn() -> None:
    rng = random.Random(1)
    for _ in range(N):
        s = _digits(rng, rng.randint(2, 19))
        assert chut.luhn(digits=s) == luhn.is_valid(s), s


def test_macie_oracle_verhoeff() -> None:
    rng = random.Random(2)
    for _ in range(N):
        s = _digits(rng, rng.randint(2, 14))
        assert chut.verhoeff(digits=s) == verhoeff.is_valid(s), s


def test_macie_oracle_cpf_cnpj() -> None:
    rng = random.Random(3)
    for _ in range(N):
        s = _digits(rng, 11)
        assert chut.cpf_mod11(digits=s) == cpf.is_valid(s), s
        s = _digits(rng, 14)
        assert chut.cnpj_mod11(digits=s) == cnpj.is_valid(s), s


def test_macie_oracle_rut() -> None:
    rng = random.Random(4)
    for _ in range(N):
        body = _digits(rng, rng.choice([7, 8]))
        assert chut.rut_check(body=body) == rut.calc_check_digit(body), body


def test_macie_oracle_nhs() -> None:
    rng = random.Random(5)
    for _ in range(N):
        s = _digits(rng, 10)
        assert chut.nhs_mod11(digits=s) == nhs.is_valid(s), s


def test_macie_oracle_iban_mod97() -> None:
    #
    # stdnum's bare ISO 7064 mod 97-10, on the IBAN rearranged as ISO
    # 13616 says: our iban_mod97 does the rearranging and letter values
    #
    rng = random.Random(6)
    for _ in range(N):
        text = (
            "".join(rng.choice(UPPER) for _ in range(2))
            + _digits(rng, 2)
            + "".join(rng.choice(UPPER + DIGITS) for _ in range(rng.randint(11, 30)))
        )
        assert chut.iban_mod97(iban=text) == mod_97_10.is_valid(text[4:] + text[:4]), (
            text
        )


def test_macie_oracle_es_id_letter() -> None:
    rng = random.Random(7)
    for _ in range(N):
        n = _digits(rng, 8)
        assert dni.calc_check_digit(n) == chut.es_id_letter(number=n), n
        m = rng.choice("XYZ") + _digits(rng, 7)
        letter = chut.es_id_letter(number=m)
        assert nie.is_valid(m + letter), m


def test_macie_oracle_fr_nir_key() -> None:
    rng = random.Random(8)
    for _ in range(N):
        department = rng.choice(["2A", "2B", _digits(rng, 2), _digits(rng, 2)])
        body = _digits(rng, 5) + department + _digits(rng, 6)
        right = nir.calc_check_digits(body)
        key = right if rng.random() < 0.5 else f"{rng.randint(0, 99):02d}"
        assert chut.fr_nir_key(nir=body + key) == (key == right), body + key


def test_macie_oracle_mx_curp_check() -> None:
    rng = random.Random(9)
    for _ in range(N):
        s = "".join(rng.choice(UPPER + DIGITS) for _ in range(17))
        assert chut.mx_curp_check(curp=s) == curp.calc_check_digit(s), s


def test_macie_oracle_it_cf_check() -> None:
    rng = random.Random(10)
    for _ in range(N):
        s = "".join(rng.choice(UPPER + DIGITS) for _ in range(15))
        assert chut.it_cf_check(code=s) == codicefiscale.calc_check_digit(s), s


@pytest.fixture(scope="module")
def cf() -> ItCfDetector:
    return ItCfDetector(config={})


def test_macie_oracle_it_organization(cf) -> None:
    #
    # the 11 digit codice fiscale of organizations is the partita IVA: the
    # detector's rules, not only its Luhn digit, match stdnum's
    #
    rng = random.Random(11)
    for _ in range(N):
        body = rng.choice(["0000000", _digits(rng, 7)]) + rng.choice(
            [f"{rng.randint(0, 130):03d}", "888", "999", _digits(rng, 3)]
        )
        number = body + rng.choice([luhn.calc_check_digit(body), _digits(rng, 1)])
        assert cf.is_organization(digits=number) == iva.is_valid(number), number
