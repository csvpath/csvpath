# Managed identifier reference

Every managed data identifier with a stand-in, from the packaged catalog
(`csvpath/macie/rulesbase/managed_identifiers.json`). This page is
generated from the catalog; `tests/macie/test_macie_docs.py` checks it
and regenerates it.

- **Keywords**: the keyword mode (`required`, `absent` or `none`) and the
  keyword list's name in the catalog, which is what a
  [project rulesbase](customizing.md) overrides.
- **Detector**: the detector's name in the catalog; a parameter after `:`
  (e.g. `iban:GB`) selects the country.
- **Fidelity**: A, Macie documents the rule; B, the format is ours from
  the issuer's published rules (see [translation](translation.md)).
- **Partial**: what the stand-in does not detect that Macie says Macie
  does.

Not supported: `NAME` and `ADDRESS`, and driver's licenses for Finland,
Greece, Hungary, Ireland, Latvia, Lithuania, Luxembourg, Malta, the
Netherlands, Poland, Portugal, Romania, Slovakia, Slovenia and Sweden
(see [limitations](limitations.md)).


## FINANCIAL_INFORMATION (58)

| Identifier | Keywords | Detector | Severity | Fidelity | Partial |
|---|---|---|---|---|---|
| `ALBANIA_BANK_ACCOUNT_NUMBER` | none | `iban:AL` | 1:HIGH | A |  |
| `ANDORRA_BANK_ACCOUNT_NUMBER` | none | `iban:AD` | 1:HIGH | A |  |
| `BANK_ACCOUNT_NUMBER` | required, `bank_account` | `bank_account` | 1:HIGH | A |  |
| `BOSNIA_AND_HERZEGOVINA_BANK_ACCOUNT_NUMBER` | none | `iban:BA` | 1:HIGH | A |  |
| `BRAZIL_BANK_ACCOUNT_NUMBER` | none | `iban:BR` | 1:HIGH | A |  |
| `BULGARIA_BANK_ACCOUNT_NUMBER` | none | `iban:BG` | 1:HIGH | A |  |
| `COSTA_RICA_BANK_ACCOUNT_NUMBER` | none | `iban:CR` | 1:HIGH | A |  |
| `CREDIT_CARD_EXPIRATION` | required, `card_expiration` | `card_expiration` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `CREDIT_CARD_MAGNETIC_STRIPE` | required, `mag_stripe` | `mag_stripe` | 1:HIGH | A |  |
| `CREDIT_CARD_NUMBER` | required, `credit_card` | `credit_card` | 1:HIGH | A |  |
| `CREDIT_CARD_NUMBER_(NO_KEYWORD)` | absent, `credit_card` | `credit_card` | 1:HIGH | A |  |
| `CREDIT_CARD_SECURITY_CODE` | required, `card_security_code` | `card_security_code` | 1:MEDIUM 2:HIGH | B |  |
| `CROATIA_BANK_ACCOUNT_NUMBER` | none | `iban:HR` | 1:HIGH | A |  |
| `CYPRUS_BANK_ACCOUNT_NUMBER` | none | `iban:CY` | 1:HIGH | A |  |
| `CZECH_REPUBLIC_BANK_ACCOUNT_NUMBER` | none | `iban:CZ` | 1:HIGH | A |  |
| `DENMARK_BANK_ACCOUNT_NUMBER` | none | `iban:DK` | 1:HIGH | A |  |
| `DOMINICAN_REPUBLIC_BANK_ACCOUNT_NUMBER` | none | `iban:DO` | 1:HIGH | A |  |
| `EGYPT_BANK_ACCOUNT_NUMBER` | none | `iban:EG` | 1:HIGH | A |  |
| `ESTONIA_BANK_ACCOUNT_NUMBER` | none | `iban:EE` | 1:HIGH | A |  |
| `FAROE_ISLANDS_BANK_ACCOUNT_NUMBER` | none | `iban:FO` | 1:HIGH | A |  |
| `FINLAND_BANK_ACCOUNT_NUMBER` | none | `iban:FI` | 1:HIGH | A |  |
| `FRANCE_BANK_ACCOUNT_NUMBER` | required, `bban_fr` | `bank:FR` | 1:HIGH | A |  |
| `GEORGIA_BANK_ACCOUNT_NUMBER` | none | `iban:GE` | 1:HIGH | A |  |
| `GERMANY_BANK_ACCOUNT_NUMBER` | required, `bban_de` | `bank:DE` | 1:HIGH | A |  |
| `GREECE_BANK_ACCOUNT_NUMBER` | none | `iban:GR` | 1:HIGH | A |  |
| `GREENLAND_BANK_ACCOUNT_NUMBER` | none | `iban:GL` | 1:HIGH | A |  |
| `HUNGARY_BANK_ACCOUNT_NUMBER` | none | `iban:HU` | 1:HIGH | A |  |
| `ICELAND_BANK_ACCOUNT_NUMBER` | none | `iban:IS` | 1:HIGH | A |  |
| `IRELAND_BANK_ACCOUNT_NUMBER` | none | `iban:IE` | 1:HIGH | A |  |
| `ITALY_BANK_ACCOUNT_NUMBER` | required, `bban_it` | `bank:IT` | 1:HIGH | A |  |
| `JORDAN_BANK_ACCOUNT_NUMBER` | none | `iban:JO` | 1:HIGH | A |  |
| `KOSOVO_BANK_ACCOUNT_NUMBER` | none | `iban:XK` | 1:HIGH | A |  |
| `LIECHTENSTEIN_BANK_ACCOUNT_NUMBER` | none | `iban:LI` | 1:HIGH | A |  |
| `LITHUANIA_BANK_ACCOUNT_NUMBER` | none | `iban:LT` | 1:HIGH | A |  |
| `MALTA_BANK_ACCOUNT_NUMBER` | none | `iban:MT` | 1:HIGH | A |  |
| `MAURITANIA_BANK_ACCOUNT_NUMBER` | none | `iban:MR` | 1:HIGH | A |  |
| `MAURITIUS_BANK_ACCOUNT_NUMBER` | none | `iban:MU` | 1:HIGH | A |  |
| `MONACO_BANK_ACCOUNT_NUMBER` | none | `iban:MC` | 1:HIGH | A |  |
| `MONTENEGRO_BANK_ACCOUNT_NUMBER` | none | `iban:ME` | 1:HIGH | A |  |
| `NETHERLANDS_BANK_ACCOUNT_NUMBER` | none | `iban:NL` | 1:HIGH | A |  |
| `NORTH_MACEDONIA_BANK_ACCOUNT_NUMBER` | none | `iban:MK` | 1:HIGH | A |  |
| `POLAND_BANK_ACCOUNT_NUMBER` | none | `iban:PL` | 1:HIGH | A |  |
| `PORTUGAL_BANK_ACCOUNT_NUMBER` | none | `iban:PT` | 1:HIGH | A |  |
| `SAN_MARINO_BANK_ACCOUNT_NUMBER` | none | `iban:SM` | 1:HIGH | A |  |
| `SENEGAL_BANK_ACCOUNT_NUMBER` | none | `iban:SN` | 1:HIGH | A |  |
| `SERBIA_BANK_ACCOUNT_NUMBER` | none | `iban:RS` | 1:HIGH | A |  |
| `SLOVAKIA_BANK_ACCOUNT_NUMBER` | none | `iban:SK` | 1:HIGH | A |  |
| `SLOVENIA_BANK_ACCOUNT_NUMBER` | none | `iban:SI` | 1:HIGH | A |  |
| `SPAIN_BANK_ACCOUNT_NUMBER` | required, `bban_es` | `bank:ES` | 1:HIGH | A |  |
| `SWEDEN_BANK_ACCOUNT_NUMBER` | none | `iban:SE` | 1:HIGH | A |  |
| `SWITZERLAND_BANK_ACCOUNT_NUMBER` | none | `iban:CH` | 1:HIGH | A |  |
| `TIMOR_LESTE_BANK_ACCOUNT_NUMBER` | none | `iban:TL` | 1:HIGH | A |  |
| `TUNISIA_BANK_ACCOUNT_NUMBER` | none | `iban:TN` | 1:HIGH | A |  |
| `TURKIYE_BANK_ACCOUNT_NUMBER` | none | `iban:TR` | 1:HIGH | A |  |
| `UKRAINE_BANK_ACCOUNT_NUMBER` | none | `iban:UA` | 1:HIGH | A |  |
| `UK_BANK_ACCOUNT_NUMBER` | required, `bban_gb` | `bank:GB` | 1:HIGH | A |  |
| `UNITED_ARAB_EMIRATES_BANK_ACCOUNT_NUMBER` | none | `iban:AE` | 1:HIGH | A |  |
| `VIRGIN_ISLANDS_BANK_ACCOUNT_NUMBER` | none | `iban:VG` | 1:HIGH | A |  |

## PERSONAL_INFORMATION (81)

| Identifier | Keywords | Detector | Severity | Fidelity | Partial |
|---|---|---|---|---|---|
| `ARGENTINA_DNI_NUMBER` | required, `ar_dni` | `ar_dni` | 1:HIGH | B |  |
| `ARGENTINA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER` | required, `ar_tax` | `ar_cuit_individual` | 1:HIGH | A |  |
| `ARGENTINA_ORGANIZATION_TAX_IDENTIFICATION_NUMBER` | required, `ar_tax` | `ar_cuit_organization` | 1:MEDIUM 100:HIGH | A |  |
| `ARGENTINA_TARJETA_SUBE` | required, `ar_sube` | `ar_sube` | 1:MEDIUM 100:HIGH | A |  |
| `AUSTRALIA_DRIVERS_LICENSE` | required, `australia_drivers_license` | `australia_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `AUSTRALIA_TAX_FILE_NUMBER` | required, `au_tfn` | `au_tfn` | 1:HIGH | A | Only 9 digit TFNs are detected, not the older 8 digit TFNs |
| `AUSTRIA_DRIVERS_LICENSE` | required, `austria_drivers_license` | `austria_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `BELGIUM_DRIVERS_LICENSE` | required, `belgium_drivers_license` | `belgium_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `BRAZIL_CEP_CODE` | required, `br_cep` | `br_cep` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `BRAZIL_CNPJ_NUMBER` | required, `brazil_tax` | `br_cnpj` | 1:HIGH | A | Brazil issues alphanumeric CNPJs from July 2026; only numeric CNPJs are detected |
| `BRAZIL_CPF_NUMBER` | required, `brazil_tax` | `br_cpf` | 1:HIGH | A |  |
| `BRAZIL_PHONE_NUMBER` | required, `br_phone` | `br_phone` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `BRAZIL_RG_NUMBER` | required, `br_rg` | `br_rg` | 1:HIGH | B |  |
| `BULGARIA_DRIVERS_LICENSE` | required, `bulgaria_drivers_license` | `bulgaria_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `CANADA_DRIVERS_LICENSE` | required, `canada_drivers_license` | `canada_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `CANADA_HEALTH_NUMBER` | required, `ca_health` | `ca_health` | 1:HIGH | B | Only British Columbia, Ontario and Quebec health numbers are detected |
| `CANADA_NATIONAL_IDENTIFICATION_NUMBER` | required, `ca_pr` | `ca_pr` | 1:HIGH | B |  |
| `CANADA_PASSPORT_NUMBER` | required, `canada_passport` | `canada_passport` | 1:MEDIUM 2:HIGH | B |  |
| `CANADA_SOCIAL_INSURANCE_NUMBER` | required, `ca_sin` | `ca_sin` | 1:HIGH | A |  |
| `CHILE_RUT_NUMBER` | required, `chile_rut` | `cl_rut` | 1:HIGH | A |  |
| `COLOMBIA_CITIZENSHIP_CARD_NUMBER` | required, `co_cedula` | `co_cedula` | 1:HIGH | B |  |
| `COLOMBIA_INDIVIDUAL_NIT_NUMBER` | required, `co_nit` | `co_nit_individual` | 1:HIGH | B |  |
| `COLOMBIA_ORGANIZATION_NIT_NUMBER` | required, `co_nit` | `co_nit_organization` | 1:MEDIUM 100:HIGH | B |  |
| `CROATIA_DRIVERS_LICENSE` | required, `croatia_drivers_license` | `croatia_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `CYPRUS_DRIVERS_LICENSE` | required, `cyprus_drivers_license` | `cyprus_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `CZECHIA_DRIVERS_LICENSE` | required, `czechia_drivers_license` | `czechia_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `DATE_OF_BIRTH` | required, `birth_date` | `birth_date` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `DENMARK_DRIVERS_LICENSE` | required, `denmark_drivers_license` | `denmark_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `DRIVERS_LICENSE` | required, `us_drivers_license` | `us_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `ESTONIA_DRIVERS_LICENSE` | required, `estonia_drivers_license` | `estonia_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `EUROPEAN_HEALTH_INSURANCE_CARD_NUMBER` | required, `eu_ehic` | `eu_ehic` | 1:HIGH | B |  |
| `FINLAND_EUROPEAN_HEALTH_INSURANCE_NUMBER` | required, `fi_ehic` | `fi_ehic` | 1:HIGH | B |  |
| `FRANCE_DRIVERS_LICENSE` | required, `france_drivers_license` | `france_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `FRANCE_HEALTH_INSURANCE_NUMBER` | required, `fr_health` | `fr_nir` | 1:HIGH | A |  |
| `FRANCE_NATIONAL_IDENTIFICATION_NUMBER` | required, `fr_nir` | `fr_nir` | 1:HIGH | A |  |
| `FRANCE_PASSPORT_NUMBER` | required, `france_passport` | `france_passport` | 1:MEDIUM 2:HIGH | B |  |
| `FRANCE_PHONE_NUMBER` | required, `phone` | `fr_phone` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `FRANCE_TAX_IDENTIFICATION_NUMBER` | required, `fr_tax` | `fr_spi` | 1:HIGH | A |  |
| `GERMANY_DRIVERS_LICENSE` | required, `germany_drivers_license` | `germany_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `GERMANY_NATIONAL_IDENTIFICATION_NUMBER` | required, `de_id` | `de_id` | 1:HIGH | B |  |
| `GERMANY_PASSPORT_NUMBER` | required, `germany_passport` | `germany_passport` | 1:MEDIUM 2:HIGH | B |  |
| `GERMANY_PHONE_NUMBER` | required, `phone` | `de_phone` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `GERMANY_TAX_IDENTIFICATION_NUMBER` | required, `de_tax` | `de_idnr` | 1:HIGH | A |  |
| `HTTP_COOKIE` | none | `http_cookie` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `INDIA_AADHAAR_NUMBER` | required, `in_aadhaar` | `in_aadhaar` | 1:HIGH | A |  |
| `INDIA_DRIVERS_LICENSE` | required, `india_drivers_license` | `india_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `INDIA_PERMANENT_ACCOUNT_NUMBER` | required, `in_pan` | `in_pan` | 1:HIGH | B |  |
| `ITALY_DRIVERS_LICENSE` | required, `italy_drivers_license` | `italy_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `ITALY_NATIONAL_IDENTIFICATION_NUMBER` | required, `it_cf` | `it_cf` | 1:HIGH | A |  |
| `ITALY_PASSPORT_NUMBER` | required, `italy_passport` | `italy_passport` | 1:MEDIUM 2:HIGH | B |  |
| `ITALY_PHONE_NUMBER` | required, `phone` | `it_phone` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `LATITUDE_LONGITUDE` | required, `lat_long` | `lat_long` | 1:LOW 2:MEDIUM | B |  |
| `MEDICAL_DEVICE_UDI` | required, `udi` | `udi` | 1:LOW 2:MEDIUM 100:HIGH | B | Only GS1 and HIBCC UDIs are detected, not ICCBBA ISBT 128 UDIs |
| `MEXICO_CURP_NUMBER` | required, `mx_curp` | `mx_curp` | 1:HIGH | A |  |
| `MEXICO_INDIVIDUAL_RFC_NUMBER` | required, `mx_rfc` | `mx_rfc_individual` | 1:HIGH | B |  |
| `MEXICO_ORGANIZATION_RFC_NUMBER` | required, `mx_rfc` | `mx_rfc_organization` | 1:MEDIUM 100:HIGH | B |  |
| `PHONE_NUMBER` | required, `phone` | `us_phone` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `SPAIN_DNI_NUMBER` | required, `es_dni` | `es_dni` | 1:HIGH | B |  |
| `SPAIN_DRIVERS_LICENSE` | required, `spain_drivers_license` | `spain_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `SPAIN_NIE_NUMBER` | required, `es_tax` | `es_nie` | 1:HIGH | A |  |
| `SPAIN_NIF_NUMBER` | required, `es_tax` | `es_nif` | 1:HIGH | B |  |
| `SPAIN_PASSPORT_NUMBER` | required, `spain_passport` | `spain_passport` | 1:MEDIUM 2:HIGH | B |  |
| `SPAIN_PHONE_NUMBER` | required, `phone` | `es_phone` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `SPAIN_TAX_IDENTIFICATION_NUMBER` | required, `es_tax` | `es_cif` | 1:HIGH | B |  |
| `UK_DRIVERS_LICENSE` | required, `uk_drivers_license` | `uk_drivers_license` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `UK_ELECTORAL_ROLL_NUMBER` | required, `gb_electoral` | `gb_electoral` | 1:HIGH | B |  |
| `UK_NATIONAL_INSURANCE_NUMBER` | required, `gb_nino` | `gb_nino` | 1:HIGH | A |  |
| `UK_NHS_NUMBER` | required, `uk_nhs` | `uk_nhs` | 1:HIGH | A |  |
| `UK_PASSPORT_NUMBER` | required, `uk_passport` | `uk_passport` | 1:MEDIUM 2:HIGH | B |  |
| `UK_PHONE_NUMBER` | required, `phone` | `gb_phone` | 1:LOW 2:MEDIUM 100:HIGH | B |  |
| `UK_TAX_IDENTIFICATION_NUMBER` | required, `gb_tax` | `gb_utr` | 1:HIGH | A | Only UTRs are detected, not TRNs (temporary reference numbers) |
| `USA_HEALTHCARE_PROCEDURE_CODE` | required, `us_hcpcs` | `us_hcpcs` | 1:HIGH | B |  |
| `USA_HEALTH_INSURANCE_CLAIM_NUMBER` | required, `us_hicn` | `us_hicn` | 1:HIGH | B | Only SSN-based HICNs are detected, not Railroad Retirement Board numbers |
| `USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER` | required, `us_itin` | `us_itin` | 1:HIGH | A |  |
| `USA_MEDICARE_BENEFICIARY_IDENTIFIER` | required, `us_mbi` | `us_mbi` | 1:HIGH | A |  |
| `USA_NATIONAL_DRUG_CODE` | required, `us_ndc` | `us_ndc` | 1:HIGH | B |  |
| `USA_NATIONAL_PROVIDER_IDENTIFIER` | required, `us_npi` | `us_npi` | 1:HIGH | A |  |
| `USA_PASSPORT_NUMBER` | required, `usa_passport` | `usa_passport` | 1:MEDIUM 2:HIGH | B |  |
| `USA_SOCIAL_SECURITY_NUMBER` | required, `us_ssn` | `us_ssn` | 1:HIGH | A |  |
| `US_DRUG_ENFORCEMENT_AGENCY_NUMBER` | required, `us_dea` | `us_dea` | 1:HIGH | A |  |
| `VEHICLE_IDENTIFICATION_NUMBER` | required, `vin` | `vin` | 1:LOW 100:MEDIUM | B |  |

## CREDENTIALS (9)

| Identifier | Keywords | Detector | Severity | Fidelity | Partial |
|---|---|---|---|---|---|
| `AWS_CREDENTIALS` | required, `aws_secret` | `aws_secret` | 1:HIGH | A |  |
| `GCP_API_KEY` | required, `gcp_api_key` | `gcp_api_key` | 1:HIGH | A |  |
| `HTTP_BASIC_AUTH_HEADER` | none | `http_basic` | 1:HIGH | A |  |
| `JSON_WEB_TOKEN` | none | `jwt` | 1:HIGH | A |  |
| `OPENSSH_PRIVATE_KEY` | none | `openssh` | 1:HIGH | A |  |
| `PGP_PRIVATE_KEY` | none | `pgp` | 1:HIGH | A |  |
| `PKCS` | none | `pkcs` | 1:HIGH | A |  |
| `PUTTY_PRIVATE_KEY` | none | `putty` | 1:HIGH | A |  |
| `STRIPE_CREDENTIALS` | none | `stripe` | 1:HIGH | A |  |

148 identifiers.
