# Ticket R2

You work on the EDI support desk that serves the sender of the file described
below. A customer has raised the ticket that follows. The partner agreement,
the sender's OFTP2 gateway trace (and, where available, its file status report),
the EDIFACT interchange in question, the partner's response and extracts from the
specifications are attached. Everything you need
is in these documents. All companies, identifiers and documents are synthetic.

## The ticket

```text
From: Robin Hale, EDI desk, Osterbrook Axle Systems
Subject: Marrowgate Motor Works says our sender ID is unknown

Since 28 October Marrowgate Motor Works rejects our invoices, saying our sender ID is unknown. We have used the same sender ID since March. I attach this morning's interchange as our gateway transmitted it (wire copy) and their CONTRL. Is something wrong on our side? Please find the root cause and tell us who has to fix it.
```

## Document 1: Partner agreement (partner_agreement.txt)

```text
PARTNER AGREEMENT: ELECTRONIC DATA INTERCHANGE
Between Osterbrook Axle Systems (the Supplier) and Marrowgate Motor Works (the Customer)
Effective 1 March 2026. Synthetic document written for this evaluation.

1. Transport: OFTP2 (RFC 5024) over TCP/IP with TLS
   Supplier ODETTE ID (SFIDORIG): O0013OSTERBROOK6232
   Customer ODETTE ID (SFIDDEST): O0013MARROWGATE5428
   Supplier gateway: oftp.osterbrook.example (198.51.100.119)
   Customer gateway: oftp.marrowgate.example (203.0.113.224)
   Protocol release level: 5 (OFTP 2.0)
   Data exchange buffer size (SSIDSDEB): 4096
   Credit (SSIDCRED): 64
   Buffer compression: no. Restart: yes. Secure authentication: no.
   File security and file compression: none (SFIDSEC 00, SFIDCOMP 0).
   Signed EERP: not required (SFIDSIGN N).
   The Customer returns an EERP for every virtual file it accepts.

2. Virtual files
   Invoices: one interchange per virtual file, dataset name (SFIDDSN) OSTERBROOK.INVOIC.
   File format U. SFIDDATE and SFIDTIME are set by the Supplier's gateway to
   the date and time the virtual file is made available for transmission.

3. EDIFACT
   Syntax identifier and version (UNB S001): UNOA, version 3.
   Supplier interchange sender ID (UNB S002 0004 / 0007): OSTERBROOK82 / ZZ
   Customer interchange recipient ID (UNB S003 0010 / 0007): MARROWGATE58 / ZZ
   Messages: INVOIC D.96A, one message per interchange.
   Interchanges are sent without line feeds between segments.
   The Customer's translator returns a CONTRL message for every rejected
   interchange, as a separate virtual file over the same OFTP2 link.

4. Support contacts
   Supplier EDI desk: Robin Hale
   Customer EDI operations: Robin Brandt
```

## Document 2: OFTP2 gateway debug trace (sender side) (oftp2_session.log)

```text
# OFTP2 gateway debug trace, Osterbrook Axle Systems (O0013OSTERBROOK6232)
# '>>' = command exchange buffer sent by this gateway, '<<' = received from the
# remote OFTP2 location. Each buffer is shown as transmitted, between [ and ]
# (Stream Transmission Header omitted, non-printable octets as \xNN).
# '..' = gateway event, '!!' = gateway warning. Passwords are masked.
# DRAFT: '??' in a reason code field marks a code not yet verified for this evaluation.
2026-10-30 06:58:44.000 ----- .. outbound TCP connect to oftp.harrowfld.example (203.0.113.238) timed out after 30 s, retry in 120 s
2026-10-30 07:01:25.000 S3254 .. session S3254: TCP connect to oftp.harrowfld.example (203.0.113.238), TLS 1.3 established
2026-10-30 07:01:25.131 S3254 << [IODETTE FTP READY \x0D]
2026-10-30 07:01:25.168 S3254 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 07:01:25.193 S3254 << [X5O0013HARROWFLD3690       ********04096BNYN064N            \x0D]
2026-10-30 07:01:25.344 S3254 .. queued INVOIC_HARROWFLD_065800.edi
2026-10-30 07:01:25.425 S3254 >> [HOSTERBROOK.INVOIC            202610300658000001        O0013HARROWFLD3690       O0013OSTERBROOK6232      U000000000000000012000000000001200000000000000000000000N000]
2026-10-30 07:01:25.484 S3254 << [200000000000000000]
2026-10-30 07:01:25.809 S3254 .. DATA: 3 exchange buffer(s), 11497 octets
2026-10-30 07:01:25.865 S3254 >> [T0000000000000000000000000000011497]
2026-10-30 07:01:26.045 S3254 << [4N]
2026-10-30 07:01:26.093 S3254 .. file transferred, awaiting EERP
2026-10-30 07:01:26.199 S3254 >> [R]
2026-10-30 07:01:26.338 S3254 << [F??000\x0D]
2026-10-30 07:01:26.443 S3254 .. session closed
2026-10-30 07:50:00.443 S3255 .. session S3255: inbound TCP connection from 203.0.113.238, TLS 1.3 established
2026-10-30 07:50:00.487 S3255 >> [IODETTE FTP READY \x0D]
2026-10-30 07:50:00.540 S3255 << [X5O0013HARROWFLD3690       ********04096BNYN064N            \x0D]
2026-10-30 07:50:00.586 S3255 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 07:50:00.712 S3255 << [EOSTERBROOK.INVOIC            202610300658000001        O0013OSTERBROOK6232      O0013HARROWFLD3690       \x00\x00\x00\x00]
2026-10-30 07:50:00.736 S3255 >> [P]
2026-10-30 07:50:00.858 S3255 .. EERP matched to INVOIC_HARROWFLD_065800.edi (sent 30 Oct 07:01): delivered
2026-10-30 07:50:01.022 S3255 << [HHARROWFLD.DELFOR             202610300750000001        O0013OSTERBROOK6232      O0013HARROWFLD3690       U000000000000000033000000000003300000000000000000000000N000]
2026-10-30 07:50:01.106 S3255 >> [200000000000000000]
2026-10-30 07:50:01.308 S3255 .. DATA: 9 exchange buffer(s), 33326 octets
2026-10-30 07:50:01.323 S3255 << [T0000000000000000000000000000033326]
2026-10-30 07:50:01.367 S3255 >> [4N]
2026-10-30 07:50:01.463 S3255 .. stored as inbound/DELFOR_HARROWFLD_075000.edi
2026-10-30 07:50:01.623 S3255 << [R]
2026-10-30 07:50:01.639 S3255 >> [EHARROWFLD.DELFOR             202610300750000001        O0013HARROWFLD3690       O0013OSTERBROOK6232      \x00\x00\x00\x00]
2026-10-30 07:50:01.682 S3255 << [P]
2026-10-30 07:50:01.817 S3255 >> [R]
2026-10-30 07:50:01.971 S3255 << [F??000\x0D]
2026-10-30 07:50:02.101 S3255 .. session closed
2026-10-30 08:24:58.000 ----- .. outbound TCP connect to oftp.ostley.example (203.0.113.159) timed out after 30 s, retry in 120 s
2026-10-30 08:27:54.000 S3248 .. session S3248: TCP connect to oftp.ostley.example (203.0.113.159), TLS 1.3 established
2026-10-30 08:27:54.038 S3248 << [IODETTE FTP READY \x0D]
2026-10-30 08:27:54.048 S3248 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 08:27:54.194 S3248 << [X5O0013OSTLEY0232          ********04096BNYN064N            \x0D]
2026-10-30 08:27:54.335 S3248 .. queued INVOIC_OSTLEY_082355.edi
2026-10-30 08:27:54.412 S3248 >> [HOSTERBROOK.INVOIC            202610300823550001        O0013OSTLEY0232          O0013OSTERBROOK6232      U000000000000000033000000000003300000000000000000000000N000]
2026-10-30 08:27:54.471 S3248 << [200000000000000000]
2026-10-30 08:27:54.556 S3248 .. DATA: 9 exchange buffer(s), 32867 octets
2026-10-30 08:27:54.658 S3248 >> [T0000000000000000000000000000032867]
2026-10-30 08:27:54.678 S3248 << [4N]
2026-10-30 08:27:54.691 S3248 .. file transferred, awaiting EERP
2026-10-30 08:27:54.866 S3248 >> [R]
2026-10-30 08:27:54.876 S3248 << [F??000\x0D]
2026-10-30 08:27:55.032 S3248 .. session closed
2026-10-30 08:42:05.000 S3256 .. session S3256: TCP connect to oftp.pemberline.example (203.0.113.125), TLS 1.3 established
2026-10-30 08:42:05.075 S3256 << [IODETTE FTP READY \x0D]
2026-10-30 08:42:05.145 S3256 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 08:42:05.287 S3256 << [X5O0013PEMBERLINE0751      ********04096BNYN064N            \x0D]
2026-10-30 08:42:05.445 S3256 .. queued INVOIC_PEMBERLINE_084048.edi
2026-10-30 08:42:05.495 S3256 >> [HOSTERBROOK.INVOIC            202610300840480001        O0013PEMBERLINE0751      O0013OSTERBROOK6232      U000000000000000057000000000005700000000000000000000000N000]
2026-10-30 08:42:05.515 S3256 << [200000000000000000]
2026-10-30 08:42:05.594 S3256 .. DATA: 15 exchange buffer(s), 57543 octets
2026-10-30 08:42:05.671 S3256 >> [T0000000000000000000000000000057543]
2026-10-30 08:42:05.817 S3256 << [4N]
2026-10-30 08:42:05.934 S3256 .. file transferred, awaiting EERP
2026-10-30 08:42:05.991 S3256 >> [R]
2026-10-30 08:42:06.171 S3256 << [F??000\x0D]
2026-10-30 08:42:06.192 S3256 .. session closed
2026-10-30 08:50:15.000 S3147 .. session S3147: TCP connect to oftp.marrowgate.example (203.0.113.224), TLS 1.3 established
2026-10-30 08:50:15.008 S3147 << [IODETTE FTP READY \x0D]
2026-10-30 08:50:15.165 S3147 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 08:50:15.274 S3147 << [X5O0013MARROWGATE5428      ********04096BNYN064N            \x0D]
2026-10-30 08:50:15.329 S3147 .. queued INV38522.edi
2026-10-30 08:50:15.427 S3147 >> [HOSTERBROOK.INVOIC            202610300849540001        O0013MARROWGATE5428      O0013OSTERBROOK6232      U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 08:50:15.599 S3147 << [200000000000000000]
2026-10-30 08:50:15.706 S3147 .. DATA: 1 exchange buffer(s), 337 octets
2026-10-30 08:50:15.723 S3147 >> [T0000000000000000000000000000000337]
2026-10-30 08:50:15.876 S3147 << [4N]
2026-10-30 08:50:15.901 S3147 .. file transferred, awaiting EERP
2026-10-30 08:50:15.925 S3147 >> [R]
2026-10-30 08:50:15.958 S3147 << [F??000\x0D]
2026-10-30 08:50:16.015 S3147 .. session closed
2026-10-30 08:58:13.032 S3249 .. session S3249: inbound TCP connection from 203.0.113.159, TLS 1.3 established
2026-10-30 08:58:13.068 S3249 >> [IODETTE FTP READY \x0D]
2026-10-30 08:58:13.184 S3249 << [X5O0013OSTLEY0232          ********04096BNYN064N            \x0D]
2026-10-30 08:58:13.211 S3249 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 08:58:13.365 S3249 << [EOSTERBROOK.INVOIC            202610300823550001        O0013OSTERBROOK6232      O0013OSTLEY0232          \x00\x00\x00\x00]
2026-10-30 08:58:13.390 S3249 >> [P]
2026-10-30 08:58:13.404 S3249 .. EERP matched to INVOIC_OSTLEY_082355.edi (sent 30 Oct 08:27): delivered
2026-10-30 08:58:13.570 S3249 << [R]
2026-10-30 08:58:13.693 S3249 >> [F??000\x0D]
2026-10-30 08:58:13.843 S3249 .. session closed
2026-10-30 08:59:46.192 S3257 .. session S3257: inbound TCP connection from 203.0.113.125, TLS 1.3 established
2026-10-30 08:59:46.367 S3257 >> [IODETTE FTP READY \x0D]
2026-10-30 08:59:46.538 S3257 << [X5O0013PEMBERLINE0751      ********04096BNYN064N            \x0D]
2026-10-30 08:59:46.569 S3257 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 08:59:46.615 S3257 << [EOSTERBROOK.INVOIC            202610300840480001        O0013OSTERBROOK6232      O0013PEMBERLINE0751      \x00\x00\x00\x00]
2026-10-30 08:59:46.775 S3257 >> [P]
2026-10-30 08:59:46.835 S3257 .. EERP matched to INVOIC_PEMBERLINE_084048.edi (sent 30 Oct 08:42): delivered
2026-10-30 08:59:47.010 S3257 << [R]
2026-10-30 08:59:47.142 S3257 >> [F??000\x0D]
2026-10-30 08:59:47.321 S3257 .. session closed
2026-10-30 09:02:28.000 S3250 .. session S3250: TCP connect to oftp.thornvale.example (203.0.113.181), TLS 1.3 established
2026-10-30 09:02:28.125 S3250 << [IODETTE FTP READY \x0D]
2026-10-30 09:02:28.205 S3250 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 09:02:28.229 S3250 << [X5O0013THORNVALE6939       ********04096BNYN064N            \x0D]
2026-10-30 09:02:28.378 S3250 .. queued INVOIC_THORNVALE_090108.edi
2026-10-30 09:02:28.546 S3250 >> [HOSTERBROOK.INVOIC            202610300901080001        O0013THORNVALE6939       O0013OSTERBROOK6232      U000000000000000026000000000002600000000000000000000000N000]
2026-10-30 09:02:28.574 S3250 << [200000000000000000]
2026-10-30 09:02:28.619 S3250 .. DATA: 7 exchange buffer(s), 25709 octets
2026-10-30 09:02:28.677 S3250 >> [T0000000000000000000000000000025709]
2026-10-30 09:02:28.746 S3250 << [4N]
2026-10-30 09:02:28.890 S3250 .. file transferred, awaiting EERP
2026-10-30 09:02:28.979 S3250 >> [R]
2026-10-30 09:02:29.018 S3250 << [F??000\x0D]
2026-10-30 09:02:29.089 S3250 .. session closed
2026-10-30 09:10:01.000 S3148 .. session S3148: inbound TCP connection from 203.0.113.224, TLS 1.3 established
2026-10-30 09:10:01.049 S3148 >> [IODETTE FTP READY \x0D]
2026-10-30 09:10:01.073 S3148 << [X5O0013MARROWGATE5428      ********04096BNYN064N            \x0D]
2026-10-30 09:10:01.182 S3148 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 09:10:01.312 S3148 << [EOSTERBROOK.INVOIC            202610300849540001        O0013OSTERBROOK6232      O0013MARROWGATE5428      \x00\x00\x00\x00]
2026-10-30 09:10:01.374 S3148 >> [P]
2026-10-30 09:10:01.484 S3148 .. EERP matched to INV38522.edi: delivered
2026-10-30 09:10:01.626 S3148 << [HMARROWGATE.CONTRL            202610300907030001        O0013OSTERBROOK6232      O0013MARROWGATE5428      U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 09:10:01.692 S3148 >> [200000000000000000]
2026-10-30 09:10:02.051 S3148 .. DATA: 1 exchange buffer(s), 190 octets
2026-10-30 09:10:02.162 S3148 << [T0000000000000000000000000000000190]
2026-10-30 09:10:02.317 S3148 >> [4N]
2026-10-30 09:10:02.387 S3148 .. stored as inbound/MARROWGATE.CONTRL_202610300907030001.edi
2026-10-30 09:10:02.558 S3148 << [R]
2026-10-30 09:10:02.631 S3148 >> [EMARROWGATE.CONTRL            202610300907030001        O0013MARROWGATE5428      O0013OSTERBROOK6232      \x00\x00\x00\x00]
2026-10-30 09:10:02.699 S3148 << [P]
2026-10-30 09:10:02.775 S3148 >> [R]
2026-10-30 09:10:02.798 S3148 << [F??000\x0D]
2026-10-30 09:10:02.831 S3148 .. session closed
2026-10-30 09:13:42.000 ----- .. outbound TCP connect to oftp.harrowfld.example (203.0.113.238) timed out after 30 s, retry in 120 s
2026-10-30 09:16:22.000 S3252 .. session S3252: TCP connect to oftp.harrowfld.example (203.0.113.238), TLS 1.3 established
2026-10-30 09:16:22.139 S3252 << [IODETTE FTP READY \x0D]
2026-10-30 09:16:22.262 S3252 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 09:16:22.292 S3252 << [X5O0013HARROWFLD3690       ********04096BNYN064N            \x0D]
2026-10-30 09:16:22.469 S3252 .. queued INVOIC_HARROWFLD_091300.edi
2026-10-30 09:16:22.480 S3252 >> [HOSTERBROOK.INVOIC            202610300913000001        O0013HARROWFLD3690       O0013OSTERBROOK6232      U000000000000000021000000000002100000000000000000000000N000]
2026-10-30 09:16:22.534 S3252 << [200000000000000000]
2026-10-30 09:16:22.688 S3252 .. DATA: 6 exchange buffer(s), 21242 octets
2026-10-30 09:16:22.747 S3252 >> [T0000000000000000000000000000021242]
2026-10-30 09:16:22.808 S3252 << [4N]
2026-10-30 09:16:22.895 S3252 .. file transferred, awaiting EERP
2026-10-30 09:16:22.986 S3252 >> [R]
2026-10-30 09:16:23.053 S3252 << [F??000\x0D]
2026-10-30 09:16:23.080 S3252 .. session closed
2026-10-30 09:58:40.080 S3253 .. session S3253: inbound TCP connection from 203.0.113.238, TLS 1.3 established
2026-10-30 09:58:40.107 S3253 >> [IODETTE FTP READY \x0D]
2026-10-30 09:58:40.205 S3253 << [X5O0013HARROWFLD3690       ********04096BNYN064N            \x0D]
2026-10-30 09:58:40.366 S3253 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 09:58:40.489 S3253 << [EOSTERBROOK.INVOIC            202610300913000001        O0013OSTERBROOK6232      O0013HARROWFLD3690       \x00\x00\x00\x00]
2026-10-30 09:58:40.526 S3253 >> [P]
2026-10-30 09:58:40.692 S3253 .. EERP matched to INVOIC_HARROWFLD_091300.edi (sent 30 Oct 09:16): delivered
2026-10-30 09:58:40.812 S3253 << [R]
2026-10-30 09:58:40.907 S3253 >> [F??000\x0D]
2026-10-30 09:58:40.992 S3253 .. session closed
2026-10-30 10:03:34.089 S3251 .. session S3251: inbound TCP connection from 203.0.113.181, TLS 1.3 established
2026-10-30 10:03:34.141 S3251 >> [IODETTE FTP READY \x0D]
2026-10-30 10:03:34.231 S3251 << [X5O0013THORNVALE6939       ********04096BNYN064N            \x0D]
2026-10-30 10:03:34.375 S3251 >> [X5O0013OSTERBROOK6232      ********04096BNYN064N            \x0D]
2026-10-30 10:03:34.397 S3251 << [EOSTERBROOK.INVOIC            202610300901080001        O0013OSTERBROOK6232      O0013THORNVALE6939       \x00\x00\x00\x00]
2026-10-30 10:03:34.521 S3251 >> [P]
2026-10-30 10:03:34.530 S3251 .. EERP matched to INVOIC_THORNVALE_090108.edi (sent 30 Oct 09:02): delivered
2026-10-30 10:03:34.617 S3251 << [HTHORNVALE.DELJIT             202610301003340001        O0013OSTERBROOK6232      O0013THORNVALE6939       U000000000000000031000000000003100000000000000000000000N000]
2026-10-30 10:03:34.646 S3251 >> [200000000000000000]
2026-10-30 10:03:34.752 S3251 .. DATA: 8 exchange buffer(s), 31584 octets
2026-10-30 10:03:34.870 S3251 << [T0000000000000000000000000000031584]
2026-10-30 10:03:35.016 S3251 >> [4N]
2026-10-30 10:03:35.126 S3251 .. stored as inbound/DELJIT_THORNVALE_100334.edi
2026-10-30 10:03:35.165 S3251 << [R]
2026-10-30 10:03:35.270 S3251 >> [ETHORNVALE.DELJIT             202610301003340001        O0013THORNVALE6939       O0013OSTERBROOK6232      \x00\x00\x00\x00]
2026-10-30 10:03:35.414 S3251 << [P]
2026-10-30 10:03:35.448 S3251 >> [R]
2026-10-30 10:03:35.598 S3251 << [F??000\x0D]
2026-10-30 10:03:35.681 S3251 .. session closed
```

## Document 3: EDIFACT interchange as transmitted (wire copy captured by the sender's gateway) (interchange.edi)

```text
UNB+UNOA:3+OSTERBROOK82:ZZ+MARROWGATE58:ZZ+261030:0849+678494'UNH+1+INVOIC:D:96A:UN'BGM+380+INV38522+9'DTM+137:20261030:102'NAD+SE+++OSTERBROOK AXLE SYSTEMS'NAD+BY+++MARROWGATE MOTOR WORKS'CUX+2:EUR:4'LIN+1++P-23708:IN'QTY+47:329'MOA+203:3266.97'PRI+AAA:9.93'UNS+S'MOA+77:3920.36'TAX+7+VAT+++:::20+S'MOA+124:653.39'UNT+15+1'UNZ+1+678494'
```

## Document 4: Partner response (partner_response.txt)

```text
From: Robin Brandt, EDI operations, Marrowgate Motor Works
To: Robin Hale, Osterbrook Axle Systems
Subject: RE: unknown sender

Hello,

Our translator rejects your interchanges as coming from an unknown sender; the CONTRL is below. We moved our translator's partner table to a new server on 27 October, and everything was migrated as it was. Please check your sender ID.

Regards,
Robin Brandt

--- CONTRL as received by Osterbrook Axle Systems (inbound/MARROWGATE.CONTRL_202610300907030001.edi) ---
UNB+UNOA:3+MARROWGATE58:ZZ+OSTERBROOK82:ZZ+261030:0907+C00770'UNH+1+CONTRL:D:3:UN'UCI+678494+OSTERBROOK82:ZZ+MARROWGATE58:ZZ+<<UNVERIFIED-PF>>+<<UNVERIFIED-PH>>+UNB+2:1'UNT+3+1'UNZ+1+C00770'
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

value: a JSON string holding the interchange sender identification that the CONTRL reports (the UNB S002 0004 value, without its qualifier).

Example of the format only (not a hint):
```json
{"cause": "file_too_large", "layer": "transport", "owner": "receiver", "location": ["SFID.SFIDFSIZ"], "next_check": "none", "value": "12345"}
```
