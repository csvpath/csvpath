"""detectors for managed data identifiers. Each takes its data from the
catalog's detectors section and finds occurrences in one cell. The
catalog's detector names map to classes here. A detector with
TAKES_PARAMETER = True gets one from its reference, e.g. "iban:GB". One
class can serve several detector names, each with its own catalog data,
e.g. GroupedDigitsDetector for ca_sin and uk_nhs, and EsIdDetector for
es_dni and es_nie."""

from .bank_account_detector import BankAccountDetector
from .cl_rut_detector import ClRutDetector
from .co_nit_detector import CoNitDetector
from .credential_detector import CredentialDetector
from .credit_card_detector import CreditCardDetector
from .de_id_detector import DeIdDetector
from .es_id_detector import EsIdDetector
from .format_detector import FormatDetector
from .fr_nir_detector import FrNirDetector
from .grouped_digits_detector import GroupedDigitsDetector
from .iban_detector import IbanDetector
from .it_cf_detector import ItCfDetector
from .mag_stripe_detector import MagStripeDetector
from .mx_curp_detector import MxCurpDetector
from .mx_rfc_detector import MxRfcDetector
from .us_id_detector import UsIdDetector
from .us_npi_detector import UsNpiDetector
from .us_ssn_detector import UsSsnDetector
from .vin_detector import VinDetector

DETECTORS = {
    "canada_passport": FormatDetector,
    "france_passport": FormatDetector,
    "germany_passport": FormatDetector,
    "italy_passport": FormatDetector,
    "spain_passport": FormatDetector,
    "uk_passport": FormatDetector,
    "usa_passport": FormatDetector,
    "aws_secret": CredentialDetector,
    "gcp_api_key": CredentialDetector,
    "http_basic": CredentialDetector,
    "jwt": CredentialDetector,
    "openssh": CredentialDetector,
    "pgp": CredentialDetector,
    "pkcs": CredentialDetector,
    "putty": CredentialDetector,
    "stripe": CredentialDetector,
    "ar_cuit_individual": GroupedDigitsDetector,
    "ar_cuit_organization": GroupedDigitsDetector,
    "ar_sube": GroupedDigitsDetector,
    "au_tfn": GroupedDigitsDetector,
    "bank": BankAccountDetector,
    "bank_account": FormatDetector,
    "card_security_code": FormatDetector,
    "br_cnpj": GroupedDigitsDetector,
    "br_cpf": GroupedDigitsDetector,
    "ca_sin": GroupedDigitsDetector,
    "cl_rut": ClRutDetector,
    "co_nit_individual": CoNitDetector,
    "co_nit_organization": CoNitDetector,
    "credit_card": CreditCardDetector,
    "de_id": DeIdDetector,
    "de_idnr": GroupedDigitsDetector,
    "es_cif": EsIdDetector,
    "es_dni": EsIdDetector,
    "es_nie": EsIdDetector,
    "es_nif": EsIdDetector,
    "fr_nir": FrNirDetector,
    "fr_spi": GroupedDigitsDetector,
    "iban": IbanDetector,
    "in_aadhaar": GroupedDigitsDetector,
    "it_cf": ItCfDetector,
    "mag_stripe": MagStripeDetector,
    "mx_curp": MxCurpDetector,
    "mx_rfc_individual": MxRfcDetector,
    "mx_rfc_organization": MxRfcDetector,
    "us_dea": UsIdDetector,
    "us_hcpcs": UsIdDetector,
    "us_hicn": UsIdDetector,
    "us_itin": UsIdDetector,
    "us_mbi": UsIdDetector,
    "us_ndc": UsIdDetector,
    "us_npi": UsNpiDetector,
    "gb_nino": FormatDetector,
    "gb_utr": GroupedDigitsDetector,
    "uk_nhs": GroupedDigitsDetector,
    "us_ssn": UsSsnDetector,
    "vin": VinDetector,
}
