# Ticket E1

You work on the EDI support desk that serves the sender of the file described
below. A customer has raised the ticket that follows. The partner agreement,
the sender's OFTP2 gateway trace (and, where available, its file status report),
the EDIFACT interchange in question, the partner's response and extracts from the
specifications are attached. Everything you need
is in these documents. All companies, identifiers and documents are synthetic.

## The ticket

```text
From: Kim Hale, EDI desk, Larkspan Body Panels
Subject: Corrandale Truck Plant rejects our invoices since their upgrade

Since 26 October Corrandale Truck Plant rejects every invoice interchange we send. For months before that the same files were accepted, and nothing has changed on our side. Corrandale Truck Plant upgraded their translator on 26 October and even say themselves it may be their problem. Our gateway shows this morning's batch delivered with an EERP. Please find the root cause and tell us who has to fix it.
```

## Document 1: Partner agreement (partner_agreement.txt)

```text
PARTNER AGREEMENT: ELECTRONIC DATA INTERCHANGE
Between Larkspan Body Panels (the Supplier) and Corrandale Truck Plant (the Customer)
Effective 1 March 2026. Synthetic document written for this evaluation.

1. Transport: OFTP2 (RFC 5024) over TCP/IP with TLS
   Supplier ODETTE ID (SFIDORIG): O0013LARKSPAN6472
   Customer ODETTE ID (SFIDDEST): O0013CORRANDALE6357
   Supplier gateway: oftp.larkspan.example (198.51.100.35)
   Customer gateway: oftp.corrandale.example (203.0.113.75)
   Protocol release level: 5 (OFTP 2.0)
   Data exchange buffer size (SSIDSDEB): 4096
   Credit (SSIDCRED): 64
   Buffer compression: no. Restart: yes. Secure authentication: no.
   File security and file compression: none (SFIDSEC 00, SFIDCOMP 0).
   Signed EERP: not required (SFIDSIGN N).
   The Customer returns an EERP for every virtual file it accepts.

2. Virtual files
   Invoices: one interchange per virtual file, dataset name (SFIDDSN) LARKSPAN.INVOIC.
   File format U. SFIDDATE and SFIDTIME are set by the Supplier's gateway to
   the date and time the virtual file is made available for transmission.

3. EDIFACT
   Syntax identifier and version (UNB S001): UNOA, version 3.
   Supplier interchange sender ID (UNB S002 0004 / 0007): LARKSPAN73 / ZZZ
   Customer interchange recipient ID (UNB S003 0010 / 0007): CORRANDALE92 / ZZZ
   Messages: INVOIC D.96A, up to 50 messages per interchange.
   Messages are sent in one functional group (UNG/UNE) per interchange.
   Interchanges are sent without line feeds between segments.
   The Customer's translator returns a CONTRL message for every rejected
   interchange, as a separate virtual file over the same OFTP2 link.

4. Support contacts
   Supplier EDI desk: Kim Hale
   Customer EDI operations: Jordan Brandt
```

## Document 2: OFTP2 gateway debug trace (sender side) (oftp2_session.log)

```text
# OFTP2 gateway debug trace, Larkspan Body Panels (O0013LARKSPAN6472)
# '>>' = command exchange buffer sent by this gateway, '<<' = received from the
# remote OFTP2 location. Each buffer is shown as transmitted, between [ and ]
# (Stream Transmission Header omitted, non-printable octets as \xNN).
# '..' = gateway event, '!!' = gateway warning. Passwords are masked.
# DRAFT: '??' in a reason code field marks a code not yet verified for this evaluation.

2026-10-30 07:26:03.000 S7351 .. session S7351: TCP connect to oftp.corrandale.example (203.0.113.75), TLS 1.3 established
2026-10-30 07:26:03.109 S7351 << [IODETTE FTP READY \x0D]
2026-10-30 07:26:03.151 S7351 >> [X5O0013LARKSPAN6472        ********04096BNYN064N            \x0D]
2026-10-30 07:26:03.251 S7351 << [X5O0013CORRANDALE6357      ********04096BNYN064N            \x0D]
2026-10-30 07:26:03.325 S7351 .. queued INVOICES_20261030_BATCH1.edi
2026-10-30 07:26:03.345 S7351 >> [HLARKSPAN.INVOIC              202610300725100001        O0013CORRANDALE6357      O0013LARKSPAN6472        U000000000000000003000000000000300000000000000000000000N000]
2026-10-30 07:26:03.373 S7351 << [200000000000000000]
2026-10-30 07:26:03.416 S7351 .. DATA: 1 exchange buffer(s), 2692 octets
2026-10-30 07:26:03.512 S7351 >> [T0000000000000000000000000000002692]
2026-10-30 07:26:03.645 S7351 << [4N]
2026-10-30 07:26:03.817 S7351 .. file transferred, awaiting EERP
2026-10-30 07:26:03.919 S7351 >> [R]
2026-10-30 07:26:03.927 S7351 << [F??000\x0D]
2026-10-30 07:26:03.937 S7351 .. session closed

2026-10-30 07:56:35.000 S7352 .. session S7352: inbound TCP connection from 203.0.113.75, TLS 1.3 established
2026-10-30 07:56:35.104 S7352 >> [IODETTE FTP READY \x0D]
2026-10-30 07:56:35.238 S7352 << [X5O0013CORRANDALE6357      ********04096BNYN064N            \x0D]
2026-10-30 07:56:35.352 S7352 >> [X5O0013LARKSPAN6472        ********04096BNYN064N            \x0D]
2026-10-30 07:56:35.456 S7352 << [ELARKSPAN.INVOIC              202610300725100001        O0013LARKSPAN6472        O0013CORRANDALE6357      \x00\x00\x00\x00]
2026-10-30 07:56:35.549 S7352 >> [P]
2026-10-30 07:56:35.725 S7352 << [HCORRANDALE.CONTRL            202610300753470001        O0013LARKSPAN6472        O0013CORRANDALE6357      U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 07:56:35.792 S7352 >> [200000000000000000]
2026-10-30 07:56:35.850 S7352 .. DATA: 1 exchange buffer(s), 188 octets
2026-10-30 07:56:35.986 S7352 << [T0000000000000000000000000000000188]
2026-10-30 07:56:36.099 S7352 >> [4N]
2026-10-30 07:56:36.155 S7352 .. stored as inbound/CORRANDALE.CONTRL_202610300753470001.edi
2026-10-30 07:56:36.332 S7352 << [R]
2026-10-30 07:56:36.374 S7352 >> [ECORRANDALE.CONTRL            202610300753470001        O0013CORRANDALE6357      O0013LARKSPAN6472        \x00\x00\x00\x00]
2026-10-30 07:56:36.503 S7352 << [P]
2026-10-30 07:56:36.595 S7352 >> [R]
2026-10-30 07:56:36.634 S7352 << [F??000\x0D]
2026-10-30 07:56:36.734 S7352 .. session closed
```

## Document 3: EDIFACT interchange the ticket is about (as transmitted) (interchange.edi)

```text
UNB+UNOA:3+LARKSPAN73:ZZZ+CORRANDALE92:ZZZ+261030:0725+00000122'UNG+INVOIC+LARKSPAN73:ZZZ+CORRANDALE92:ZZZ+261030:0725+8984+UN+D:96A'UNH+1+INVOIC:D:96A:UN'BGM+380+INV76944+9'DTM+137:20261030:102'NAD+SE+++LARKSPAN BODY PANELS'NAD+BY+++CORRANDALE TRUCK PLANT'CUX+2:EUR:4'LIN+1++P-17631:IN'QTY+47:268'MOA+203:8007.84'PRI+AAA:29.88'LIN+2++P-70828:IN'QTY+47:31'MOA+203:261.95'PRI+AAA:8.45'LIN+3++P-40416:IN'QTY+47:91'MOA+203:1668.03'PRI+AAA:18.33'UNS+S'MOA+77:11925.38'TAX+7+VAT+++:::20+S'MOA+124:1987.56'UNT+23+1'UNH+2+INVOIC:D:96A:UN'BGM+380+INV76945+9'DTM+137:20261030:102'NAD+SE+++LARKSPAN BODY PANELS'NAD+BY+++CORRANDALE TRUCK PLANT'CUX+2:EUR:4'LIN+1++P-94902:IN'QTY+47:345'MOA+203:11353.95'PRI+AAA:32.91'LIN+2++P-58891:IN'QTY+47:222'MOA+203:8027.52'PRI+AAA:36.16'LIN+3++P-81844:IN'QTY+47:202'MOA+203:4886.38'PRI+AAA:24.19'UNS+S'MOA+77:29121.42'TAX+7+VAT+++:::20+S'MOA+124:4853.57'UNT+23+2'UNH+3+INVOIC:D:96A:UN'BGM+380+INV76946+9'DTM+137:20261030:102'NAD+SE+++LARKSPAN BODY PANELS'NAD+BY+++CORRANDALE TRUCK PLANT'CUX+2:EUR:4'LIN+1++P-09289:IN'QTY+47:235'MOA+203:4949.10'PRI+AAA:21.06'LIN+2++P-48418:IN'QTY+47:43'MOA+203:1570.79'PRI+AAA:36.53'LIN+3++P-90697:IN'QTY+47:285'MOA+203:7581.00'PRI+AAA:26.60'UNS+S'MOA+77:16921.06'TAX+7+VAT+++:::20+S'MOA+124:2820.17'UNT+23+3'UNH+4+INVOIC:D:96A:UN'BGM+380+INV76947+9'DTM+137:20261030:102'NAD+SE+++LARKSPAN BODY PANELS'NAD+BY+++CORRANDALE TRUCK PLANT'CUX+2:EUR:4'LIN+1++P-78769:IN'QTY+47:42'MOA+203:1832.04'PRI+AAA:43.62'LIN+2++P-19554:IN'QTY+47:279'MOA+203:9078.66'PRI+AAA:32.54'UNS+S'MOA+77:13092.84'TAX+7+VAT+++:::20+S'MOA+124:2182.14'UNT+19+4'UNH+5+INVOIC:D:96A:UN'BGM+380+INV76948+9'DTM+137:20261030:102'NAD+SE+++LARKSPAN BODY PANELS'NAD+BY+++CORRANDALE TRUCK PLANT'CUX+2:EUR:4'LIN+1++P-85386:IN'QTY+47:214'MOA+203:8352.42'PRI+AAA:39.03'LIN+2++P-30351:IN'QTY+47:110'MOA+203:2932.60'PRI+AAA:26.66'LIN+3++P-09224:IN'QTY+47:341'MOA+203:7423.57'PRI+AAA:21.77'UNS+S'MOA+77:22450.30'TAX+7+VAT+++:::20+S'MOA+124:3741.71'UNT+23+5'UNH+6+INVOIC:D:96A:UN'BGM+380+INV76949+9'DTM+137:20261030:102'NAD+SE+++LARKSPAN BODY PANELS'NAD+BY+++CORRANDALE TRUCK PLANT'CUX+2:EUR:4'LIN+1++P-35732:IN'QTY+47:355'MOA+203:13095.95'PRI+AAA:36.89'LIN+2++P-22768:IN'QTY+47:54'MOA+203:901.80'PRI+AAA:16.70'LIN+3++P-87640:IN'QTY+47:338'MOA+203:15646.02'PRI+AAA:46.29'UNS+S'MOA+77:35572.52'TAX+7+VAT+++:::20+S'MOA+124:5928.75'UNT+23+6'UNH+7+INVOIC:D:96A:UN'BGM+380+INV76950+9'DTM+137:20261030:102'NAD+SE+++LARKSPAN BODY PANELS'NAD+BY+++CORRANDALE TRUCK PLANT'CUX+2:EUR:4'LIN+1++P-49380:IN'QTY+47:202'MOA+203:8029.50'PRI+AAA:39.75'LIN+2++P-83492:IN'QTY+47:378'MOA+203:17055.36'PRI+AAA:45.12'UNS+S'MOA+77:30101.83'TAX+7+VAT+++:::20+S'MOA+124:5016.97'UNT+19+7'UNE+7+8984'UNZ+1+122'
```

## Document 4: Partner response (partner_response.txt)

```text
From: Jordan Brandt, EDI operations, Corrandale Truck Plant
To: Kim Hale, Larkspan Body Panels
Subject: Rejected interchange this morning

Hello,

Our translator rejected your interchange of this morning; the CONTRL we returned over OFTP2 is copied below. As far as we can tell it is about your UNZ: you sent us 7 invoices but your UNZ control count says 1. This started after we upgraded our translator on 26 October, so it may be on our side, but please check your files too.

Regards,
Jordan Brandt

--- CONTRL as received by Larkspan Body Panels (inbound/CORRANDALE.CONTRL_202610300753470001.edi) ---
UNB+UNOA:3+CORRANDALE92:ZZZ+LARKSPAN73:ZZZ+261030:0753+C55401'UNH+1+CONTRL:D:3:UN'UCI+00000122+LARKSPAN73:ZZZ+CORRANDALE92:ZZZ+<<UNVERIFIED-PF>>+<<UNVERIFIED-PG>>+UNZ'UNT+3+1'UNZ+1+C55401'
```

## Document 5: Specification extracts (spec_extracts.txt)

```text
RFC 5024 (ODETTE File Transfer Protocol 2), section 4.3.6. Verbatim extract.

4.3.6.  End to End Response (EERP)

   The End to End Response (EERP) command notifies the originator of a
   Virtual File that the Virtual File has been successfully delivered to
   its final destination.  This allows the originator to perform house
   keeping tasks such as deleting copies of the delivered data.

   If the originator of the Virtual File requested a signed EERP in the
   SFID, the EERP must be signed.  Signing allows the originator of the
   file to prove that the EERP was generated by the final destination.
   If the final destination is unable to sign the EERP, it may send back
   an unsigned EERP.  It is an implementation issue to allow the
   acceptance of an unsigned EERP if a signed EERP is requested.

   A Response Command must be sent from the location performing the
   final processing or distribution of the data to the originator.  The
   Response is mandatory and may be sent in the same or in any
   subsequent session.

   When an intermediate location broadcasts or distributes a Virtual
   File, it must receive a Response command from all the locations to
   which it forwarded the data before sending its own Response.  This
   ensures that the Response received by the Virtual File's originator
   accounts for all the destination locations.  An intermediate location
   therefore needs to track the status of files it processes over time.

   The requesting of a signed EERP is incompatible with the use of
   broadcast facilities because an EERP can be signed by only one
   destination.  If this scenario occurs, the intermediate broadcast
   location may continue and ignore the request for a signed EERP or
   send back a NERP.

   Example: Point to Point

      Location A sends file Ba to location B, which will send an EERP to
      location A after it successfully receives the file.

         o----------o                          o-----------o
         | Loc. A   |----------- S1 ---------->| Loc. B    |
         |          |                          |           |
         | [Ba]     |<---------- R2 -----------| [Ba]      |
         +----------o                          o-----------o

                     Key:   S - File Transfer
                            R - Response EERP
                         [Ba] - File for B from A

   Example: Data distribution

      Location A sends a Virtual File containing data for distribution
      to locations B and C via clearing centres E1 and E2.  Clearing
      centre E1 must wait for a response from E2 (for file Ba) and
      location C before it sends its response, R8, to location A.
      Clearing centre E2 can only send response R7 to E1 when location B
      acknowledges file Ba with response R6.

   o---------o        o---------o        o---------o        o---------o
   | Loc. A  |-- S1 ->| Loc. E1 |-- S2 ->| Loc. E2 |-- S5 ->| Loc. B  |
   |         |        |         |        |         |        |         |
   | [Ba,Ca] |<- R8 --| [Ba,Ca] |<- R7 --| [Ba]    |<- R6 --| [Ba]    |
   o---------o        o---------o        o---------o        o---------o
                         A   |
                         |   |           o---------o
                         |   +----- S3 ->| Loc. C  |
                         |               |         |
                         +--------- R4 --| [Ca]    |
                                         o---------o

   Example: Data collection

      Locations A and B send files Ca and Cb to clearing centre E1,
      which forwards both files to location C in a single Virtual File.
      When it receives response R4 from C, clearing centre E1 sends
      response R5 to location A and R6 to location B.

         o---------o        o---------o        o---------o
         | Loc. A  |-- S1 ->| Loc. E1 |-- S3 ->| Loc. C  |
         |         |        |         |        |         |
         | [Ca]    |<- R5 --| [Ca,Cb] |<- R4 --| [Ca,Cb] |
         o---------o        o---------o        o---------o
                               A   |
         o---------o           |   |
         | Loc. B  |-- S2 -----+   |
         |         |               |
         | [Cb]    |<- R6 ---------+
         o---------o

UN/EDIFACT syntax version 3: service segment and code list extracts.
Prepared for this eval from the sources listed at the end. Segment layouts are
restated in a compact form; code values and their names are quoted exactly.

Provenance by part:
  Parts 1 to 4 (syntax rules: UNB, UNZ, UNG, UNE, omission and truncation)
    UNECE. The segment specifications are in Annex B of the syntax rules; the
    general omission and truncation rules are in clauses 7.2 and 7.3. The text
    was prepared from the UNECE 1990 reprint (syntax version 2) and checked
    element by element against the UNECE syntax version 3 (1992) material on
    3 Nov 2026. Points that differ in version 3 are marked "(v3)".
  Parts 5 to 7 (CONTRL: UCI, S011, code lists 0083 and 0085)
    The CONTRL D.3 document hosted by ISO/TC 154/JWG 1.
  Parts 8 and 9 (service code lists 0035 and 0007)
    The service code lists hosted by ISO/TC 154/JWG 1.

1. Interchange header UNB (UNECE, Annex B)

   Data elements in order (status M = mandatory, C = conditional):
     1  S001 SYNTAX IDENTIFIER                      M
          0001 Syntax identifier          a4   M  (e.g. UNOA, UNOB, UNOC)
          0002 Syntax version number      n1   M  (v3: 3 for the 1992 rules)
     2  S002 INTERCHANGE SENDER                     M
          0004 Sender identification      an..35 M
          0007 Partner identification code qualifier  an..4 C
          0008 Address for reverse routing an..14 C
     3  S003 INTERCHANGE RECIPIENT                  M
          0010 Recipient identification   an..35 M
          0007 Partner identification code qualifier  an..4 C
          0014 Routing address            an..14 C
     4  S004 DATE/TIME OF PREPARATION               M
          0017 Date                       n6   M  (YYMMDD)
          0019 Time                       n4   M  (HHMM)
     5  0020 INTERCHANGE CONTROL REFERENCE  an..14 M  (unique reference assigned by sender)
     6  S005 RECIPIENT'S REFERENCE/PASSWORD          C
          0022 Recipient's reference/password an..14 M
          0025 Recipient's reference/password qualifier an2 C
     7  0026 APPLICATION REFERENCE          an..14 C
     8  0029 PROCESSING PRIORITY CODE       a1     C
     9  0031 ACKNOWLEDGEMENT REQUEST        n1     C  (1 = acknowledgement requested)
    10  0032 COMMUNICATIONS AGREEMENT ID    an..35 C
    11  0035 TEST INDICATOR                 n1     C  (1 = the interchange is a test)

2. Interchange trailer UNZ (UNECE, Annex B)

     1  0036 INTERCHANGE CONTROL COUNT      n..6   M
          The number of messages in the interchange or, if functional
          groups are used, the number of functional groups.
     2  0020 INTERCHANGE CONTROL REFERENCE  an..14 M
          Shall be identical to 0020 in UNB.

3. Functional group header UNG and trailer UNE (UNECE, Annex B)

   UNG: 1 0038 Functional group identification; 2 S006 Application sender's
        identification (0040, 0007); 3 S007 Application recipient's
        identification (0044, 0007); 4 S004 Date/time of preparation;
        5 0048 Functional group reference number; 6 0051 Controlling agency;
        7 S008 Message version (0052, 0054, 0057); 8 0058 Application password
        (conditional).
   UNE: 1 0060 Number of messages in the group; 2 0048 Functional group
        reference number, identical to 0048 in UNG.

4. Omission and truncation of data elements (UNECE, clauses 7.2 and 7.3)

   If a conditional data element is omitted and is followed by another data
   element, its position is indicated by retaining its data element separator.
   If one or more conditional data elements at the end of a segment are
   omitted, the segment may be truncated by the segment terminator; trailing
   data element separators are then not transmitted.

5. CONTRL message version D release 3 (UNH message identifier
   CONTRL:D:3:UN), segment UCI INTERCHANGE RESPONSE (JWG 1-hosted CONTRL D.3)

   Pos  Tag   Name                                         St  Format
   010  0020  INTERCHANGE CONTROL REFERENCE                M   an..14
   020  S002  INTERCHANGE SENDER                           M
              0004 Sender identification                   M   an..35
              0007 Identification code qualifier           C   an..4
              0008 Address for reverse routing             C   an..14
   030  S003  INTERCHANGE RECIPIENT                        M
              0010 Recipient identification                M   an..35
              0007 Identification code qualifier           C   an..4
              0014 Routing address                         C   an..14
   040  0083  ACTION, CODED                                M   an..3
   050  0085  SYNTAX ERROR, CODED                          C   an..3
   060  0013  SERVICE SEGMENT TAG, CODED                   C   a3
   070  S011  DATA ELEMENT IDENTIFICATION                  C
              0098 Erroneous data element position in segment   M  n..3
              0104 Erroneous component data element position    C  n..3

   S011 identifies the position of an erroneous data element.

6. Code list 0083 Action, coded (JWG 1-hosted CONTRL D.3)

   4   This level and all lower levels rejected
   7   This level acknowledged, next lower level acknowledged if not
       explicitly rejected
   8   Interchange received

7. Code list 0085 Syntax error, coded (JWG 1-hosted CONTRL D.3)

   2   Syntax version or level not supported
   7   Interchange recipient not actual recipient
   12  Invalid value
   13  Missing
   14  Value not supported in this position
   15  Not supported in this position
   16  Too many constituents
   17  No agreement
   18  Unspecified error
   19  Invalid decimal notation
   20  Character invalid as service character
   21  Invalid character(s)
   22  Invalid service character(s)
   23  Unknown Interchange sender
   24  Too old
   25  Test indicator not supported
   26  Duplicate detected
   27  Security function not supported
   28  References do not match
   29  Control count does not match number of instances received
   30  Functional groups and messages mixed
   31  More than one message type in group
   32  Lower level empty
   33  Invalid occurrence outside message or functional group
   34  Nesting indicator not allowed
   35  Too many segment repetitions
   36  Too many segment group repetitions
   37  Invalid type of character(s)
   38  Missing digit in front of decimal sign
   39  Data element too long
   40  Data element too short
   41  Permanent communication network error
   42  Temporary communication network error
   43  Unknown interchange recipient

8. Code list 0035 Test indicator (JWG 1-hosted service code list)

   1   Interchange is a test

9. Code list 0007 Identification code qualifier (JWG 1-hosted service code
   list; the one value used here)

   ZZZ Mutually defined

Sources
- UNECE, UN/EDIFACT syntax rules, 1990 amended reprint (syntax version 2), with
  Annex B segment specifications (UNB, UNZ, UNG, UNE; clauses 7.2 and 7.3 on
  omission and truncation):
  https://unece.org/fileadmin/DAM/trade/edifact/untdid/d422_s.htm
- UNECE, UN/EDIFACT syntax implementation guidelines, issue 94.2 (syntax
  version 3: version number 3 for the 1992 rules; UNZ count of functional
  groups):
  https://unece.org/fileadmin/DAM/trade/untdid/texts/d423.htm
- CONTRL, Syntax and service report message, version D release 3, revision 1,
  97-03-17 (UCI, S011, code lists 0083 and 0085), hosted by ISO/TC 154/JWG 1:
  https://service.gefeg.com/jwg1/Files/v3-Contrl.pdf
- Service code lists 0035 and 0007 (D.22B archive), hosted by ISO/TC 154/JWG 1:
  https://service.gefeg.com/jwg1/Archive-Sx/D22B/cl/cl7.htm
  https://service.gefeg.com/jwg1/Archive-Sx/D22B/cl/cl3.htm
```

## What to return

Diagnose the single root cause of this ticket. Reply in any form you like,
but end your reply with exactly one fenced ```json block holding an object
with these six keys. Only the last ```json block in your reply is graded.
Give one value per key: a key that holds several options, or a list of
alternatives, scores zero for that key.

cause: exactly one of
  authentication_failure: The OFTP2 session could not be established because a password, identification code or secure authentication check failed.
  certificate_problem: A TLS or file-security certificate is expired, untrusted or not the one in the agreement.
  character_set_violation: The interchange contains characters outside the agreed syntax identifier's character repertoire.
  compression_not_agreed: A file was sent compressed (or uncompressed) contrary to what the receiver accepts.
  duplicate_interchange: An interchange was rejected because its interchange control reference was already received from this sender.
  duplicate_virtual_file: A virtual file was refused because a virtual file with the same identification was already delivered.
  end_to_end_response_not_returned: The file was delivered but the final recipient never returned the end-to-end response.
  envelope_element_format_invalid: A UNB or UNZ data element has a value whose format or length the syntax version declared in UNB S001 does not allow.
  file_too_large: The file exceeds a size limit of the receiver.
  idoc_awaiting_processing: Inbound IDocs were created in the receiver's SAP system but were not passed to the application, because the scheduled processing that should pick them up did not run.
  idoc_mapping_error: The receiver's EDI converter mapped a correct interchange to an incorrect IDoc.
  interchange_control_count_mismatch: The interchange control count in UNZ does not match the number of messages in the interchange.
  interchange_control_reference_mismatch: The interchange control reference in UNB and in UNZ are not identical.
  intermediary_fault: A clearing centre or other intermediate location lost, altered or misrouted the file.
  invalid_destination: The OFTP2 destination of the virtual file is not known to the receiver.
  no_sender_side_fault: Nothing the sender transmitted or configured is wrong, the fault lies with the receiver, and no more specific cause in this list applies.
  not_yet_determinable: The documents fit more than one root cause equally well, so the root cause cannot be named until a further check is made.
  receiver_partner_setup_missing: The receiver has not set up the sender as agreed (EDI converter partner mapping or SAP partner profile).
  recipient_identification_mismatch: The interchange recipient identification or its qualifier in UNB is not the one in the partner agreement.
  restart_position_invalid: A restarted transfer used a restart position that is wrong, or resumed from a position other than the one the receiver confirmed.
  sap_master_data_error: Posting in the receiver's SAP system failed because of its master data (material, vendor, purchase order).
  sender_identification_mismatch: The interchange sender identification or its qualifier in UNB is not the one in the partner agreement.
  session_parameters_not_negotiated: The sender used an OFTP2 session parameter (credit, buffer size or similar) outside what was negotiated.
  syntax_identifier_not_agreed: UNB S001 declares a syntax identifier or syntax version other than the agreed one.
  test_indicator_mismatch: The interchange is flagged as test (or production) contrary to the agreement.

layer: exactly one of
  transport: The OFTP2 session or file transfer, including any intermediate location.
  envelope: The EDIFACT interchange envelope (UNB to UNZ), wherever the receiver checks it (gateway or translator).
  application: The business application side, on either party: an EDI converter or SAP IDoc processing.
  none: Only with cause no_sender_side_fault: the fault is on the receiver's side, outside the layers above.
  undetermined: Only with cause not_yet_determinable.

owner: exactly one of (who must act to fix the root cause)
  sender: The party that sent the file and raised the ticket must fix it.
  receiver: The trading partner the file is addressed to must fix it.
  intermediary: A clearing centre or other intermediate location between the parties must fix it.
  agreement: The partner agreement itself is wrong or inconsistent and must be amended before either side can fix the fault.
  undetermined: Only with cause not_yet_determinable.

location: a JSON array of strings.
List the OFTP2 fields, EDIFACT data elements or application objects, on whichever
side, whose values or settings must be changed to fix the root cause, and no
others. If the fault is a conflict between two values that must agree, list both.
Write each one as:
  OFTP2 field:                 COMMAND.FIELD, e.g. "SSID.SSIDCODE"
  EDIFACT simple data element: SEGMENT.ELEMENT, e.g. "UNH.0062"
  EDIFACT component element:   SEGMENT.COMPOSITE.COMPONENT, e.g. "UNB.S003.0010"
  Application-side object:     APP.<OBJECT>, one of CONVERTER_PARTNER_TABLE, CONVERTER_MAPPING, PARTNER_PROFILE, PROCESS_CODE, BACKGROUND_JOB, MASTER_DATA, PORT
  None of the above must change: "NONE" on its own.
  Root cause not yet determinable: "UNDETERMINED" on its own.

next_check: exactly one of (the single check that would decide the root cause if the documents do not; "none" if they do)
  none: The documents already determine the root cause.
  request_receiver_gateway_log: Ask the receiver for its OFTP2 gateway log covering the file in question.
  request_receiver_translator_log: Ask the receiver for its translator's validation log for the interchange.
  request_transmitted_copy: Obtain the file exactly as the sender's gateway transmitted it, not the archived copy.
  request_other_gateway_node_trace: Obtain the trace from the sender's other gateway node or nodes.
  request_agreement_in_force: Obtain the signed version of the partner agreement currently in force.
  request_clearing_centre_trace: Ask the clearing centre for its trace of the file.
  check_sender_clock: Check the sender gateway's system clock.
  check_certificates: Check the TLS and file-security certificates on both sides.
  resend_unchanged: Send the same file again unchanged.
  resend_with_new_identity: Send the file again as a new virtual file.

value: a JSON string holding the number of INVOIC messages in the interchange, as a plain integer.

Example of the format only (not a hint):
```json
{"cause": "file_too_large", "layer": "transport", "owner": "receiver", "location": ["SFID.SFIDFSIZ"], "next_check": "none", "value": "12345"}
```
