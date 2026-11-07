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
from stdnum.ar import cuit
from stdnum.au import tfn
from stdnum.br import cnpj, cpf
from stdnum.ca import bc_phn
from stdnum.cl import rut
from stdnum.co import nit
from stdnum.de import idnr
from stdnum.es import cif, dni, nie
from stdnum.fr import nif as fr_nif
from stdnum.fr import nir
from stdnum.gb import nhs, utr
from stdnum.iso7064 import mod_11_10, mod_97_10
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


def test_macie_oracle_de_idnr() -> None:
    #
    # half the inputs get stdnum's MOD 11,10 digit, so both the digit and
    # the repeated-digit rule are exercised
    #
    rng = random.Random(12)
    for _ in range(N):
        body = _digits(rng, 10)
        check = mod_11_10.calc_check_digit(body) if rng.random() < 0.5 else ""
        number = body + (check or _digits(rng, 1))
        assert chut.de_idnr(digits=number) == idnr.is_valid(number), number


def test_macie_oracle_ar_cuit() -> None:
    #
    # stdnum also checks the type; compare only the check digit
    #
    rng = random.Random(13)
    for _ in range(N):
        body = _digits(rng, 10)
        right = cuit.calc_check_digit(body)
        digit = right if rng.random() < 0.5 else _digits(rng, 1)
        assert chut.ar_cuit(digits=body + digit) == (digit == right), body + digit


def test_macie_oracle_au_tfn() -> None:
    rng = random.Random(14)
    for _ in range(N):
        s = _digits(rng, 9)
        assert chut.au_tfn(digits=s) == tfn.is_valid(s), s


def test_macie_oracle_ca_bc_phn() -> None:
    rng = random.Random(21)
    for _ in range(N):
        body = "9" + _digits(rng, 8)
        last = bc_phn.calc_check_digit(body[1:]) if rng.random() < 0.5 else ""
        s = body + (last if len(last) == 1 else _digits(rng, 1))
        if rng.random() < 0.1:
            s = _digits(rng, 10)
        assert chut.ca_bc_phn(digits=s) == bc_phn.is_valid(s), s


def test_macie_oracle_gb_utr() -> None:
    rng = random.Random(15)
    for _ in range(N):
        rest = _digits(rng, 9)
        first = utr.calc_check_digit(rest) if rng.random() < 0.5 else _digits(rng, 1)
        assert chut.gb_utr(digits=first + rest) == utr.is_valid(first + rest), rest


def test_macie_oracle_es_cif() -> None:
    rng = random.Random(16)
    for _ in range(N):
        head = rng.choice(chut.ES_CIF_TYPES) + _digits(rng, 7)
        right = cif.calc_check_digits(head)
        last = rng.choice([right[0], right[1], rng.choice(DIGITS + "JABCDEFGHI")])
        assert chut.es_cif(cif=head + last) == cif.is_valid(head + last), head + last


def test_macie_oracle_co_nit() -> None:
    rng = random.Random(17)
    for _ in range(N):
        body = _digits(rng, rng.randint(7, 15))
        check = nit.calc_check_digit(body) if rng.random() < 0.5 else _digits(rng, 1)
        assert chut.co_nit(digits=body + check) == nit.is_valid(body + check), body


def test_macie_oracle_fr_spi() -> None:
    rng = random.Random(18)
    for _ in range(N):
        head = _digits(rng, 10)
        tail = fr_nif.calc_check_digits(head) if rng.random() < 0.5 else _digits(rng, 3)
        number = head + tail
        assert chut.fr_spi(digits=number) == fr_nif.is_valid(number), number
