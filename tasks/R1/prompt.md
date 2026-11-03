# Ticket R1

You work on the EDI support desk that serves the sender of the file described
below. A customer has raised the ticket that follows. The partner agreement,
the sender's OFTP2 gateway trace (and, where available, its file status report),
the EDIFACT interchange in question, the partner's response and extracts from the
specifications are attached. Everything you need
is in these documents. All companies, identifiers and documents are synthetic.

## The ticket

```text
From: Chris Brandt, EDI desk, Tidewell Seating Components
Subject: TRANSMISSION ERROR on every invoice to Corrandale Truck Plant

Since 15 October every invoice we send to Corrandale Truck Plant is refused with 'TRANSMISSION ERROR - PLEASE RETRANSMIT'. We retransmitted invoice INV49387 twice this morning with the same result, and one connection attempt timed out. Corrandale Truck Plant say our OFTP2 set-up or our certificate is faulty. Our network team says the link is fine. On 14 October we moved to a new release of our EDI suite (OFTP2 gateway and translator); IT tells me the configuration and the maps were migrated unchanged. Please find the root cause and tell us who has to fix it.
```

## Document 1: Partner agreement (partner_agreement.txt)

```text
PARTNER AGREEMENT: ELECTRONIC DATA INTERCHANGE
Between Tidewell Seating Components (the Supplier) and Corrandale Truck Plant (the Customer)
Effective 1 March 2026. Synthetic document written for this evaluation.

1. Transport: OFTP2 (RFC 5024) over TCP/IP with TLS
   Supplier ODETTE ID (SFIDORIG): O0013TIDEWELL3275
   Customer ODETTE ID (SFIDDEST): O0013CORRANDALE6539
   Supplier gateway: oftp.tidewell.example (198.51.100.95)
   Customer gateway: oftp.corrandale.example (203.0.113.31)
   Protocol release level: 5 (OFTP 2.0)
   Data exchange buffer size (SSIDSDEB): 4096
   Credit (SSIDCRED): 64
   Buffer compression: no. Restart: yes. Secure authentication: no.
   File security and file compression: none (SFIDSEC 00, SFIDCOMP 0).
   Signed EERP: not required (SFIDSIGN N).
   The Customer returns an EERP for every virtual file it accepts.

2. Virtual files
   Invoices: one interchange per virtual file, dataset name (SFIDDSN) TIDEWELL.INVOIC.
   File format U. SFIDDATE and SFIDTIME are set by the Supplier's gateway to
   the date and time the virtual file is made available for transmission.

3. EDIFACT
   Syntax identifier and version (UNB S001): UNOA, version 3.
   Supplier interchange sender ID (UNB S002 0004 / 0007): TIDEWELL16 / ZZ
   Customer interchange recipient ID (UNB S003 0010 / 0007): CORRANDALE49 / ZZ
   Messages: INVOIC D.96A, one message per interchange.
   Interchanges are sent without line feeds between segments.
   The Customer's gateway routes each interchange on receipt to the receiving
   plant's translator by the UNB recipient ID.
   The Customer does not return CONTRL messages.

4. Support contacts
   Supplier EDI desk: Chris Brandt
   Customer EDI operations: Morgan Lindqvist

5. Testing
   Test files go to the Customer's test gateway, ODETTE ID O0013CORRANDALETEST; production
   files go to the production ODETTE ID in section 1. UNB 0035 (test indicator)
   is set to 1 in test interchanges only. The production gateway accepts
   production interchanges only.
```

## Document 2: OFTP2 gateway debug trace (sender side) (oftp2_session.log)

```text
# OFTP2 gateway debug trace, Tidewell Seating Components (O0013TIDEWELL3275)
# '>>' = command exchange buffer sent by this gateway, '<<' = received from the
# remote OFTP2 location. Each buffer is shown as transmitted, between [ and ]
# (Stream Transmission Header omitted, non-printable octets as \xNN).
# '..' = gateway event, '!!' = gateway warning. Passwords are masked.
# DRAFT: '??' in a reason code field marks a code not yet verified for this evaluation.

2026-10-30 06:24:05.000 S5858 .. session S5858: TCP connect to oftp.corrandale.example (203.0.113.31), TLS 1.3 established
2026-10-30 06:24:05.079 S5858 << [IODETTE FTP READY \x0D]
2026-10-30 06:24:05.217 S5858 >> [X5O0013TIDEWELL3275        ********16384BNYN128N            \x0D]
2026-10-30 06:24:05.349 S5858 << [X5O0013CORRANDALE6539      ********04096BNYN064N            \x0D]
2026-10-30 06:24:05.349 S5858 !! local TLS certificate CN=oftp.tidewell.example expires 2026-11-04T23:59:59Z (5 days)
2026-10-30 06:24:05.528 S5858 .. queued INV49387.edi
2026-10-30 06:24:05.697 S5858 >> [HTIDEWELL.INVOIC              202610300623480001        O0013CORRANDALE6539      O0013TIDEWELL3275        U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 06:24:05.776 S5858 << [200000000000000000]
2026-10-30 06:24:05.866 S5858 .. DATA: 1 exchange buffer(s), 408 octets
2026-10-30 06:24:05.912 S5858 >> [T0000000000000000000000000000000408]
2026-10-30 06:24:06.041 S5858 << [5??038TRANSMISSION ERROR - PLEASE RETRANSMIT]
2026-10-30 06:24:06.216 S5858 .. file refused by partner at end of file
2026-10-30 06:24:06.241 S5858 >> [R]
2026-10-30 06:24:06.307 S5858 << [F??000\x0D]
2026-10-30 06:24:06.382 S5858 .. session closed

2026-10-30 06:53:43.000 ----- .. outbound TCP connect to oftp.corrandale.example (203.0.113.31) timed out after 30 s, retry in 120 s

2026-10-30 06:56:42.000 S5860 .. session S5860: TCP connect to oftp.corrandale.example (203.0.113.31), TLS 1.3 established
2026-10-30 06:56:42.178 S5860 << [IODETTE FTP READY \x0D]
2026-10-30 06:56:42.351 S5860 >> [X5O0013TIDEWELL3275        ********16384BNYN128N            \x0D]
2026-10-30 06:56:42.487 S5860 << [X5O0013CORRANDALE6539      ********04096BNYN064N            \x0D]
2026-10-30 06:56:42.487 S5860 !! local TLS certificate CN=oftp.tidewell.example expires 2026-11-04T23:59:59Z (5 days)
2026-10-30 06:56:42.636 S5860 .. queued INV49387.edi (retransmission 1)
2026-10-30 06:56:42.815 S5860 >> [HTIDEWELL.INVOIC              202610300653380002        O0013CORRANDALE6539      O0013TIDEWELL3275        U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 06:56:42.947 S5860 << [200000000000000000]
2026-10-30 06:56:43.093 S5860 .. DATA: 1 exchange buffer(s), 408 octets
2026-10-30 06:56:43.111 S5860 >> [T0000000000000000000000000000000408]
2026-10-30 06:56:43.198 S5860 << [5??038TRANSMISSION ERROR - PLEASE RETRANSMIT]
2026-10-30 06:56:43.210 S5860 .. file refused by partner at end of file
2026-10-30 06:56:43.333 S5860 >> [R]
2026-10-30 06:56:43.382 S5860 << [F??000\x0D]
2026-10-30 06:56:43.400 S5860 .. session closed

2026-10-30 07:33:54.000 S5861 .. session S5861: TCP connect to oftp.corrandale.example (203.0.113.31), TLS 1.3 established
2026-10-30 07:33:54.023 S5861 << [IODETTE FTP READY \x0D]
2026-10-30 07:33:54.089 S5861 >> [X5O0013TIDEWELL3275        ********16384BNYN128N            \x0D]
2026-10-30 07:33:54.244 S5861 << [X5O0013CORRANDALE6539      ********04096BNYN064N            \x0D]
2026-10-30 07:33:54.244 S5861 !! local TLS certificate CN=oftp.tidewell.example expires 2026-11-04T23:59:59Z (5 days)
2026-10-30 07:33:54.337 S5861 .. queued INV49387.edi (retransmission 2)
2026-10-30 07:33:54.383 S5861 >> [HTIDEWELL.INVOIC              202610300733410003        O0013CORRANDALE6539      O0013TIDEWELL3275        U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 07:33:54.481 S5861 << [200000000000000000]
2026-10-30 07:33:54.574 S5861 .. DATA: 1 exchange buffer(s), 408 octets
2026-10-30 07:33:54.676 S5861 >> [T0000000000000000000000000000000408]
2026-10-30 07:33:54.852 S5861 << [5??038TRANSMISSION ERROR - PLEASE RETRANSMIT]
2026-10-30 07:33:54.884 S5861 .. file refused by partner at end of file
2026-10-30 07:33:54.921 S5861 >> [R]
2026-10-30 07:33:55.097 S5861 << [F??000\x0D]
2026-10-30 07:33:55.263 S5861 .. session closed
```

## Document 3: EDIFACT interchange the ticket is about (as transmitted) (interchange.edi)

```text
UNB+UNOA:3+TIDEWELL16:ZZ+CORRANDALE49:ZZ+261030:0733+674946++++++1'UNH+1+INVOIC:D:96A:UN'BGM+380+INV49387+9'DTM+137:20261030:102'NAD+SE+++TIDEWELL SEATING COMPONENTS'NAD+BY+++CORRANDALE TRUCK PLANT'CUX+2:EUR:4'LIN+1++P-98587:IN'QTY+47:189'MOA+203:9054.99'PRI+AAA:47.91'LIN+2++P-69389:IN'QTY+47:368'MOA+203:6377.44'PRI+AAA:17.33'UNS+S'MOA+77:18518.91'TAX+7+VAT+++:::20+S'MOA+124:3086.48'UNT+19+1'UNZ+1+674946'
```

## Document 4: Partner response (partner_response.txt)

```text
From: Morgan Lindqvist, EDI operations, Corrandale Truck Plant
To: Chris Brandt, Tidewell Seating Components
Subject: RE: TRANSMISSION ERROR

Hello,

Our gateway has refused your files with a transmission error since 15 October. Your sessions also no longer offer the buffer size and credit in our agreement. Please check your OFTP2 set-up and the TLS certificate on your side; our monitoring shows it expires on 4 November. Files from our other suppliers arrive normally.

Regards,
Morgan Lindqvist
```

## Document 5: Specification extracts (spec_extracts.txt)

```text
RFC 5024 (ODETTE File Transfer Protocol 2), section 5.3.2. Verbatim extract.

5.3.2.  SSID - Start Session

   o-------------------------------------------------------------------o
   |       SSID        Start Session                                   |
   |                                                                   |
   |       Start Session Phase     Initiator <---> Responder           |
   |-------------------------------------------------------------------|
   | Pos | Field     | Description                           | Format  |
   |-----+-----------+---------------------------------------+---------|
   |   0 | SSIDCMD   | SSID Command 'X'                      | F X(1)  |
   |   1 | SSIDLEV   | Protocol Release Level                | F 9(1)  |
   |   2 | SSIDCODE  | Initiator's Identification Code       | V X(25) |
   |  27 | SSIDPSWD  | Initiator's Password                  | V X(8)  |
   |  35 | SSIDSDEB  | Data Exchange Buffer Size             | V 9(5)  |
   |  40 | SSIDSR    | Send / Receive Capabilities (S/R/B)   | F X(1)  |
   |  41 | SSIDCMPR  | Buffer Compression Indicator (Y/N)    | F X(1)  |
   |  42 | SSIDREST  | Restart Indicator (Y/N)               | F X(1)  |
   |  43 | SSIDSPEC  | Special Logic Indicator (Y/N)         | F X(1)  |
   |  44 | SSIDCRED  | Credit                                | V 9(3)  |
   |  47 | SSIDAUTH  | Secure Authentication (Y/N)           | F X(1)  |
   |  48 | SSIDRSV1  | Reserved                              | F X(4)  |
   |  52 | SSIDUSER  | User Data                             | V X(8)  |
   |  60 | SSIDCR    | Carriage Return                       | F X(1)  |
   o-------------------------------------------------------------------o

      SSIDCMD   Command Code
      Character

      Value: 'X'  SSID Command identifier.

   SSIDLEV   Protocol Release Level                           Numeric(1)

             Used to specify the level of the ODETTE-FTP protocol

      Value: '1' for Revision 1.2
             '2' for Revision 1.3
             '4' for Revision 1.4
             '5' for Revision 2.0

             Future release levels will have higher numbers.  The
             protocol release level is negotiable, with the lowest level
             being selected.

             Note: ODETTE File Transfer Protocol 1.3 (RFC 2204)
                   specifies '1' for the release level, despite adhering
                   to revision 1.3.

   SSIDCODE  Initiator's Identification Code                  String(25)

    Format:  See Identification Code (Section 5.4)

             Uniquely identifies the Initiator (sender) participating in
             the ODETTE-FTP session.

             It is an application implementation issue to link the
             expected [X.509] certificate to the SSIDCODE provided.

   SSIDPSWD  Initiator's Password                              String(8)

             Key to authenticate the sender.  Assigned by bilateral
             agreement.

   SSIDSDEB  Data Exchange Buffer Size                        Numeric(5)

    Minimum: 128
    Maximum: 99999

             The length, in octets, of the largest Data Exchange Buffer
             that can be accepted by the location.  The length includes
             the command octet but does not include the Stream
             Transmission Header.

             After negotiation, the smallest size will be selected.

   SSIDSR    Send / Receive Capabilities                       Character

      Value: 'S'  Location can only send files.
             'R'  Location can only receive files.
             'B'  Location can both send and receive files.

             Sending and receiving will be serialised during the
             session, so parallel transmissions will not take place in
             the same session.

             An error occurs if adjacent locations both specify the send
             or receive capability.

   SSIDCMPR  Buffer Compression Indicator                      Character

      Value: 'Y'  The location can handle OFTP data buffer compression
             'N'  The location cannot handle OFTP buffer compression

             Compression is only used if supported by both locations.

             The compression mechanism referred to here applies to each
             individual OFTP data buffer.  This is different from the
             file compression mechanism in OFTP, which involves the
             compression of whole files.

   SSIDREST  Restart Indicator                                 Character

      Value: 'Y'  The location can handle the restart of a partially
                  transmitted file.
             'N'  The location cannot restart a file.

   SSIDSPEC  Special Logic Indicator                           Character

      Value: 'Y'  Location can handle Special Logic
             'N'  Location cannot handle Special Logic

             Special Logic is only used if supported by both locations.

             The Special Logic extensions are only useful to access an
             X.25 network via an asynchronous entry and are not
             supported for TCP/IP connections.

   SSIDCRED  Credit                                           Numeric(3)

    Maximum: 999

             The number of consecutive Data Exchange Buffers sent by the
             Speaker before it must wait for a Credit (CDT) command from
             the Listener.

             The credit value is only applied to Data flow in the Data
             Transfer phase.

             The Speaker's available credit is initialised to SSIDCRED
             when it receives a Start File Positive Answer (SFPA)
             command from the Listener.  It is zeroed by the End File
             (EFID) command.

             After negotiation, the smallest size must be selected in
             the answer of the Responder, otherwise a protocol error
             will abort the session.

             Negotiation of the "credit-window-size" parameter.

             Window Size m  -- SSID ------------>
                            <------------ SSID --  Window Size n
                                                  (n less than or
                                                   equal to m)
             Note: negotiated value will be "n".

   SSIDAUTH  Secure Authentication                             Character

      Value: 'Y'  The location requires secure authentication.  'N'  The
             location does not require secure authentication.

             Secure authentication is only used if agreed by both
             locations.

             If the answer of the Responder does not match with the
             authentication requirements of the Initiator, then the
             Initiator must abort the session.

             No negotiation of authentication is allowed.

             authentication p  -- SSID ------------>
                               <------------ SSID --  authentication q

             p == q -> continue.
             p != q -> abort.

   SSIDRSV1  Reserved                                          String(4)

             This field is reserved for future use.

   SSIDUSER  User Data                                         String(8)

             May be used by ODETTE-FTP in any way.  If unused, it should
             be initialised to spaces.  It is expected that a bilateral
             agreement exists as to the meaning of the data.

   SSIDCR    Carriage Return                                   Character

      Value: Character with hex value '0D' or '8D'.

RFC 5024 (ODETTE File Transfer Protocol 2), section 5.3.8. Verbatim extract.

5.3.8.  EFID - End File

   o-------------------------------------------------------------------o
   |       EFID        End File                                        |
   |                                                                   |
   |       End File Phase             Speaker ----> Listener           |
   |-------------------------------------------------------------------|
   | Pos | Field     | Description                           | Format  |
   |-----+-----------+---------------------------------------+---------|
   |   0 | EFIDCMD   | EFID Command, 'T'                     | F X(1)  |
   |   1 | EFIDRCNT  | Record Count                          | V 9(17) |
   |  18 | EFIDUCNT  | Unit Count                            | V 9(17) |
   o-------------------------------------------------------------------o

   EFIDCMD   Command Code                                      Character

      Value: 'T'  EFID Command identifier.

   EFIDRCNT  Record Count                                    Numeric(17)

    Maximum: 99999999999999999

             For SSIDFMT 'F' or 'V', the exact record count.
             For SSIDFMT 'U' or 'T', zeros.

             The count will express the real size of the file (before
             buffer compression, header not included).  The total count
             is always used, even during restart processing.

   EFIDUCNT  Unit Count                                      Numeric(17)

    Maximum: 99999999999999999

             Exact number of units (octets) transmitted.

             The count will express the real size of the file.  The
             total count is always used, even during restart processing.

RFC 5024 (ODETTE File Transfer Protocol 2), section 5.3.10. Verbatim extract.

5.3.10.  EFNA - End File Negative Answer

   o-------------------------------------------------------------------o
   |       EFNA        End File Negative Answer                        |
   |                                                                   |
   |       End File Phase             Speaker <---- Listener           |
   |-------------------------------------------------------------------|
   | Pos | Field     | Description                           | Format  |
   |-----+-----------+---------------------------------------+---------|
   |   0 | EFNACMD   | EFNA Command, '5'                     | F X(1)  |
   |   1 | EFNAREAS  | Answer Reason                         | F 9(2)  |
   |   3 | EFNAREASL | Answer Reason Text Length             | V 9(3)  |
   |   6 | EFNAREAST | Answer Reason Text                    | V T(n)  |
   o-------------------------------------------------------------------o

   EFNACMD   Command Code                                      Character

      Value: '5'  EFNA Command identifier.

   EFNAREAS  Answer Reason                                    Numeric(2)

      Value: '01'  Invalid filename.
             '02'  Invalid destination.
             '03'  Invalid origin.
             '04'  Storage record format not supported.
             '05'  Maximum record length not supported.
             '06'  File size is too big.
             '10'  Invalid record count.
             '11'  Invalid byte count.
             '12'  Access method failure.
             '13'  Duplicate file.
             '14'  File direction refused.
             '15'  Cipher suite not supported.
             '16'  Encrypted file not allowed.
             '17'  Unencrypted file not allowed.
             '18'  Compression not allowed.
             '19'  Signed file not allowed.
             '20'  Unsigned file not allowed.
             '21'  Invalid file signature.
             '22'  File decryption failure.
             '23'  File decompression failure.
             '99'  Unspecified reason.

             Reason why transmission failed.

   EFNAREASL Answer Reason Text Length                        Numeric(3)

             Length in octets of the field EFNAREAST.

             0 indicates that no EFNAREAST field follows.

   EFNAREAST Answer Reason Text                               [UTF-8](n)

             Reason why transmission failed in plain text.

             It is encoded using [UTF-8].

             Maximum length of the encoded reason is 999 octets.

             No general structure is defined for this attribute.

UN/EDIFACT syntax version 3: service segment and code list extracts.
Prepared for this eval from the sources listed at the end. Segment layouts are
restated in a compact form; code values and their names are quoted exactly.

1. Interchange header UNB (syntax version 3)

   Data elements in order (status M = mandatory, C = conditional):
     1  S001 SYNTAX IDENTIFIER                      M
          0001 Syntax identifier          a4   M  (e.g. UNOA, UNOB, UNOC)
          0002 Syntax version number      n1   M  (3 for syntax version 3)
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

2. Interchange trailer UNZ

     1  0036 INTERCHANGE CONTROL COUNT      n..6   M
          The number of messages in the interchange or, if functional groups
          are used, the number of functional groups.
     2  0020 INTERCHANGE CONTROL REFERENCE  an..14 M
          Shall be identical to 0020 in UNB.

3. Functional group header UNG and trailer UNE

   UNG: 1 0038 Functional group identification; 2 S006 Application sender's
        identification (0040, 0007); 3 S007 Application recipient's
        identification (0044, 0007); 4 S004 Date/time of preparation;
        5 0048 Functional group reference number; 6 0051 Controlling agency;
        7 S008 Message version (0052, 0054, 0057); 8 0058 Application password.
   UNE: 1 0060 Number of messages in the group; 2 0048 Functional group
        reference number, identical to 0048 in UNG.

4. Omission and truncation of data elements

   If a conditional data element is omitted and is followed by another data
   element, its position is indicated by retaining its data element separator.
   If one or more conditional data elements at the end of a segment are
   omitted, the segment may be truncated by the segment terminator; trailing
   data element separators are then not transmitted.

5. CONTRL message (UNH message identifier CONTRL:D:3:UN), segment UCI
   INTERCHANGE RESPONSE

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

6. Code list 0083 Action, coded

   4   This level and all lower levels rejected
   7   This level acknowledged, next lower level acknowledged if not
       explicitly rejected
   8   Interchange received

7. Code list 0085 Syntax error, coded

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

8. Code list 0035 Test indicator

   1   Interchange is a test

Sources
- UN/EDIFACT syntax rules and Annex B segment specifications (UNB, UNZ, UNG,
  UNE; clauses 7.2 and 7.3 on omission and truncation), UNECE:
  https://unece.org/fileadmin/DAM/trade/edifact/untdid/d422_s.htm
- UN/EDIFACT syntax implementation guidelines, UNECE (syntax version number 3
  for the 1992 syntax rules; UNZ count of functional groups):
  https://unece.org/fileadmin/DAM/trade/untdid/texts/d423.htm
- CONTRL, Syntax and service report message, version D release 3 (UCI, S011,
  code lists 0083 and 0085), ISO/TC 154/JWG 1:
  https://service.gefeg.com/jwg1/Files/v3-Contrl.pdf
- Service code list 0035, ISO/TC 154/JWG 1:
  https://service.gefeg.com/jwg1/Archive-Sx/D22B/cl/cl7.htm
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

value: a JSON string holding the UNB segment exactly as the sender should transmit it for this interchange, from "UNB" up to and including its segment terminator.

Example of the format only (not a hint):
```json
{"cause": "file_too_large", "layer": "transport", "owner": "receiver", "location": ["SFID.SFIDFSIZ"], "next_check": "none", "value": "12345"}
```
