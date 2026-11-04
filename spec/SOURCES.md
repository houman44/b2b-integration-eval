# Specification sources

## RFC 5024, ODETTE File Transfer Protocol 2 (IETF, November 2007)

- Retrieved 30 Oct 2026 from https://www.rfc-editor.org/rfc/rfc5024.txt
- SHA-256 of the retrieved text: 6411a2761da53deb63ba027caaf4e3bb15e883fe418a5f7a7c9f04aa5d5c4fa2
- `spec/rfc5024/*.txt` are verbatim section extracts cut by `spec/extract_rfc5024.py`
  (page footers and running headers removed, nothing else changed).
- Licence: IETF Trust Legal Provisions; RFC text may be reproduced with attribution.

## UN/EDIFACT syntax version 3: syntax rules (UNECE) and CONTRL (JWG 1-hosted CONTRL D.3)

`spec/unedifact/syntax3_service_extracts.txt` is a prepared extract, not a verbatim copy:
segment layouts are restated compactly; code values and names are quoted exactly.
Prepared on 3 Nov 2026. Provenance is recorded per part, and per syntax version.

### Syntax rules: UNECE

Used for UNB, UNZ, UNG, UNE, composite S004 and the omission and truncation rule.

- UNECE, UN/EDIFACT syntax rules, 1990 amended reprint, with Annex B segment
  specifications and clauses 7.2 and 7.3:
  https://unece.org/fileadmin/DAM/trade/edifact/untdid/d422_s.htm.
  **This text is syntax version 2** (it sets 0002 to 2).
- UNECE, UN/EDIFACT syntax implementation guidelines, issue 94.2:
  https://unece.org/fileadmin/DAM/trade/untdid/texts/d423.htm.
  **This is the syntax version 3 source**: the 1992 rules use syntax version number 3,
  and the first UNZ element is the number of functional groups if that facility is used.

What is established for syntax version 3, element by element:

| Claim | Version 2 text (d422) | Version 3 basis |
|---|---|---|
| UNB S001, S002, S003, S004, 0020 | yes | Confirmed by Houman on 3 Nov 2026 against the syntax version 3 UNB definition |
| UNB optional trailing fields S005 to 0035, in that order | yes | Confirmed by Houman on 3 Nov 2026 against the syntax version 3 UNB definition |
| S004 0017 n6 YYMMDD, 0019 n4 HHMM | yes | Confirmed by Houman on 3 Nov 2026 (date/time) |
| UNB 0002 = 3 | no (v2 sets 2) | UNECE d423 |
| UNZ 0036, 0020 layout | yes | Not yet confirmed: no syntax version 3 layout text in hand |
| UNZ 0036 counts functional groups when used | no | UNECE d423 |
| UNG, UNE layout | yes | Not yet confirmed: no syntax version 3 layout text in hand |
| Omission and truncation (clauses 7.2, 7.3) | yes | Not yet confirmed for syntax version 3 |

### CONTRL: the CONTRL D.3 document hosted by ISO/TC 154/JWG 1

Used for every CONTRL-specific layout and code list: segment UCI, composite S011, code
lists 0083 and 0085, and the message identifier CONTRL:D:3:UN.

- CONTRL, Syntax and service report message, version D, release 3, revision 1,
  97-03-17, source Syntax Development Group, hosted by ISO/TC 154/JWG 1 (the joint
  ISO and UNECE syntax group): https://service.gefeg.com/jwg1/Files/v3-Contrl.pdf

### Service code lists 0035 and 0007: hosted by ISO/TC 154/JWG 1

- 0035 Test indicator (code 1): https://service.gefeg.com/jwg1/Archive-Sx/D22B/cl/cl7.htm
- 0007 Identification code qualifier (code ZZZ "Mutually defined"; the list has no ZZ):
  https://service.gefeg.com/jwg1/Archive-Sx/D22B/cl/cl3.htm.
  The tickets used ZZ until 3 Nov 2026 and use ZZZ since, on Houman's ruling.

### Not covered by any source above

- How S011 0098 and 0104 count positions (general knowledge).

## SAP (Amendment 1)

- Facts only, no SAP documentation text. Rule 3 condition met: on 3 Nov 2026 Houman
  confirmed that the SAP knowledge used is public SAP behaviour and his general experience,
  not OpenText or GXS material.
- That confirmation is about provenance. It does not by itself verify each SAP detail.
  IDoc statuses 53, 56 and 64, report RBDAPP01 and partner type LI (vendor) are recorded in
  `generator/codes.py` as **standard SAP conventions, not directly verified against an SAP
  source**. The LI interpretation in particular is a convention, not a verified fact.

## Verification status

Entries in `generator/codes.py` stay unverified until Houman checks them, and a release
build refuses to run until then. Verified on 3 Nov 2026: EDIFACT.LAYOUT.UNB,
EDIFACT.LAYOUT.UNB_TAIL, EDIFACT.UNB.S004_FORMAT_SYNTAX3.
