# Specification sources

## RFC 5024, ODETTE File Transfer Protocol 2 (IETF, November 2007)

- Retrieved 30 Oct 2026 from https://www.rfc-editor.org/rfc/rfc5024.txt
- SHA-256 of the retrieved text: 6411a2761da53deb63ba027caaf4e3bb15e883fe418a5f7a7c9f04aa5d5c4fa2
- `spec/rfc5024/*.txt` are verbatim section extracts cut by `spec/extract_rfc5024.py`
  (page footers and running headers removed, nothing else changed).
- Licence: IETF Trust Legal Provisions; RFC text may be reproduced with attribution.

## UN/EDIFACT syntax version 3 service segments and CONTRL (UNECE, ISO/TC 154/JWG 1)

- `spec/unedifact/syntax3_service_extracts.txt` is a prepared extract, not a verbatim
  copy: segment layouts are restated compactly; code values and names are quoted
  exactly. Prepared on 3 Nov 2026 from:
  - UNECE, UN/EDIFACT syntax rules with Annex B segment specifications (UNB, UNZ,
    UNG, UNE; clauses 7.2 and 7.3 on omission and truncation):
    https://unece.org/fileadmin/DAM/trade/edifact/untdid/d422_s.htm.
    This page is the 1990 amended reprint (syntax version 2). The extract uses it
    for syntax version 3 on the basis of the next source, which states that the
    1992 rules use syntax version number 3. TO CHECK (Houman): that the UNB, UNZ,
    UNG and UNE elements used here are unchanged in syntax version 3.
  - UNECE, UN/EDIFACT syntax implementation guidelines, issue 94.2:
    https://unece.org/fileadmin/DAM/trade/untdid/texts/d423.htm
    (syntax version number 3; the UNZ count is the number of functional groups
    if that facility is used).
  - ISO/TC 154/JWG 1 (the joint ISO and UNECE syntax group), CONTRL Syntax and
    service report message, version D, release 3, revision 1, 97-03-17:
    https://service.gefeg.com/jwg1/Files/v3-Contrl.pdf (UCI, S011, code lists
    0083 and 0085).
  - ISO/TC 154/JWG 1, service code list 0035 (D.22B archive):
    https://service.gefeg.com/jwg1/Archive-Sx/D22B/cl/cl7.htm
- Not covered by any source above, still general knowledge: how S011 0098 and
  0104 count positions; the use of 0007 qualifier "ZZ" (the JWG 1 list,
  https://service.gefeg.com/jwg1/Archive-Sx/D22B/cl/cl3.htm, has "ZZZ Mutually
  defined" and no "ZZ").
- Every entry in `generator/codes.py` stays unverified until Houman checks it,
  and a release build refuses to run until then.
