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

Houman checked every element below against the UNECE syntax version 3 (1992) material
on 3 Nov 2026. The segment specifications are in Annex B; the general omission and
truncation rules are in clauses 7.2 and 7.3.

What is established for syntax version 3, element by element:

| Claim | Version 2 text (d422) | Version 3 basis |
|---|---|---|
| UNB S001, S002, S003, S004, 0020: mandatory, in that order | yes | Annex B, confirmed by Houman on 3 Nov 2026 |
| UNB conditional elements S005 to 0035, in the specified order | yes | Annex B, confirmed by Houman on 3 Nov 2026 |
| S004 0017 n6 YYMMDD, 0019 n4 HHMM | yes | Annex B, confirmed by Houman on 3 Nov 2026 |
| UNB 0002 = 3 | no (v2 sets 2) | UNECE d423 |
| UNZ 0036 then 0020; 0020 matches UNB 0020 | yes | Annex B, confirmed by Houman on 3 Nov 2026 |
| UNZ 0036 counts messages, or functional groups if used | no | UNECE d423; Annex B, confirmed by Houman on 3 Nov 2026 |
| UNG 0038, S006, S007, S004, 0048, 0051, S008, conditional 0058 | yes | Annex B, confirmed by Houman on 3 Nov 2026 |
| UNE 0060 then 0048; 0048 matches UNG 0048 | yes | Annex B, confirmed by Houman on 3 Nov 2026 |
| Omission: an omitted conditional element followed by a present one keeps its separator | yes | Clause 7.2, confirmed by Houman on 3 Nov 2026 |
| Truncation: trailing conditional elements may be omitted by ending the segment; trailing separators not required | yes | Clause 7.3, confirmed by Houman on 3 Nov 2026 |

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

Every entry in `generator/codes.py` is now verified by Houman (3 Nov 2026), and the
release build runs. Each verdict keeps its scope (`verification` in `codes.py`):

- OFTP2 reason codes; UCI layout; CONTRL message identifier; 0083 = 4; 0085 = 2, 18, 23
  and 28 (explanation for 28 amended); S011 position counting; 0035 = 1: correct.
- 0007 = ZZZ: correct as the standard code. The partner agreements now state that both
  IDs are mutually defined between the parties, hence qualifier ZZZ.
- SAP IDoc statuses 53, 56, 64 and report RBDAPP01: correct as general SAP conventions.
- SAP partner type LI: correct as a convention. Its use in a ticket rests on the IDoc
  control record field SNDPRT, which the S1 IDoc list now names as its source.
- INVOIC D.96A body: partially verified. The fixture-specific content (segment choice,
  qualifiers, amounts) was not independently checked. The body is never graded and the
  planted fault is never in it.
- The syntax rule items (UNB, UNZ, UNG, UNE, S004, clauses 7.2 and 7.3): see the table above.
