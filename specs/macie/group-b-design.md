# Group B managed identifiers: design proposal

Status: **proposal for David's review** (2026-11-05). Nothing here is built.

Group B is "format plus keyword": identifiers with a recognizable shape but
no check digit, where Macie's keyword does most of the work. There are about
60 of them (inventory in `worklist.md` item 6). The question is how to
express them without 60 hand-written classes, and without raw regexes in
the catalog JSON that nobody can review.

## Proposal: a small format notation in the catalog

The catalog already has one: `GroupedDigitsDetector`'s `formats` use `#` for
a digit (`###.###.###-##` for a CPF). Group B extends that notation and
puts the formats in the detector's data:

| Symbol | Means |
|---|---|
| `#` | a digit |
| `A` | a letter A-Z (either case) |
| `X` | a letter or digit |
| `[ABC]` | one of these characters |
| `{n}` after a symbol | n of them, e.g. `#{9}` |
| any other character | itself, e.g. `-` or a space |

A new `FormatDetector` compiles each format to a regex once, at load, and
finds any of a detector's formats in a cell, with the usual rule that an
occurrence must not touch other letters or digits. Formats are data, so
adding a country is a catalog edit plus tests, not code.

### Worked examples

The formats below illustrate the notation. They are from memory, not yet
checked against the issuers; each will be confirmed from an issuer source
(and python-stdnum where it has the identifier) when it is built.

**UK National Insurance number** (`UK_NATIONAL_INSURANCE_NUMBER`):

```json
"gb_nino": {
  "formats": ["AA######[ABCD]", "AA ## ## ## [ABCD]"],
  "exclude_prefixes": ["BG", "GB", "KN", "NK", "NT", "TN", "ZZ"],
  "first_letter_not": "DFIQUV", "second_letter_not": "DFIOQUV"
}
```

`AB123456C` and `AB 12 34 56 C` are found; `GB123456A` is not. The
letter rules are HMRC's and are data too.

**US and Canada bank account** (`BANK_ACCOUNT_NUMBER`): Macie says 9-17
digits with no spaces, so `"formats": ["#{9,17}"]` (one range form, `{m,n}`).

**Passports**, one detector entry per country:

| Country | Formats |
|---|---|
| US | `#{9}`, `A#{8}` |
| UK | `#{9}` |
| Canada | `AA#{6}` |
| France | `##AA#{5}` |
| Germany | `[CFGHJKLMNPRTVWXYZ]X{8}` |
| Italy | `AA#{7}` |
| Spain | `AAA#{6}` |

**Driver's licenses**: one entry per country, and the **US entry is the
union of the state formats** (`A#{7}`, `#{9}`, `A#{12}`, `AA#{6}`, ...).
Macie has one US identifier, not one per state, so the union is the same
granularity. Near a "driver's license" keyword, any state's format counts.

## What the notation does not cover

These get small code validators, named in the data the way `check` names a
`ChecksumUtility` method today:

| Identifier | Validator |
|---|---|
| `DATE_OF_BIRTH`, `CREDIT_CARD_EXPIRATION` | a real date in one of Macie's listed shapes (`02/26`, `Feb 2026`, `26-Feb`, `expY=2026, expM=02`) |
| `LATITUDE_LONGITUDE` | a decimal-degree pair, latitude within ±90 and longitude within ±180 |
| `HTTP_COOKIE` | a complete `Cookie:` or `Set-Cookie:` header with name=value pairs; no keyword |
| phone numbers (7) | see below |

## Phone numbers need a new keyword mode

Macie: "If a keyword is in proximity of the data, the number doesn't have to
include a country code. If a keyword isn't in proximity of the data, the
number has to include a country code." That is neither `required` nor
`none`. Proposal: a fourth `keyword_mode`, `required_or_prefix`, where
the detector says whether an occurrence carries its country code (`+44`,
`0044`). This stays inside the Macie package (`ManagedIdentifier`); there is
no core change.

## Group C

`NAME` and `ADDRESS` stay "no stand-in", which the converter already
reports as not translated. Macie uses ML for names. An address needs a
gazetteer of places and postal codes.

## Order, if agreed

1. `FormatDetector` and the notation, with UK NINO, US/Canada bank account
   and credit card security code as the first entries.
2. Passports (7).
3. Phone numbers (7) and `required_or_prefix`.
4. Dates: birth date and card expiration.
5. Driver's licenses (32; the US union is the biggest single piece).
6. The rest: GPS, HTTP cookie, Brazil CEP, Canada PR card, India PAN,
   Brazil RG, Argentina DNI, Colombia cedula, UK electoral roll.

Each step is one PR with a normative pair, like group A.

## Questions for David

1. Format notation in the catalog, as above, rather than code-defined forms
   per family (group A's style) or raw regexes in JSON?
2. The US driver's license as one union of state formats?
3. A new `required_or_prefix` keyword mode for phone numbers?
