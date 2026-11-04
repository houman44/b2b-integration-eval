# Ticket U1

You work on the EDI support desk that serves the sender of the file described
below. A customer has raised the ticket that follows. The partner agreement,
the sender's OFTP2 gateway trace (and, where available, its file status report),
the EDIFACT interchange in question, the partner's response and extracts from the
specifications are attached. Everything you need
is in these documents. All companies, identifiers and documents are synthetic.

## The ticket

```text
From: Dana Brandt, EDI desk, Quillmere Drivetrain Ltd
Subject: Velbrook Vehicle Assembly refuses a brand-new invoice as a duplicate

This morning Velbrook Vehicle Assembly refused invoice INV58106 with 'DUPLICATE FILE', twice. It is a brand-new invoice, created at 09:25 today, and our gateway trace (attached, from gw1) shows it was never sent before. Our earlier invoice today went through. Their duplicate check must be broken. Please find the root cause and tell us who has to fix it.
```

## Document 1: Partner agreement (partner_agreement.txt)

```text
PARTNER AGREEMENT: ELECTRONIC DATA INTERCHANGE
Between Quillmere Drivetrain Ltd (the Supplier) and Velbrook Vehicle Assembly (the Customer)
Effective 1 March 2026. Synthetic document written for this evaluation.

1. Transport: OFTP2 (RFC 5024) over TCP/IP with TLS
   Supplier ODETTE ID (SFIDORIG): O0013QUILLMERE9940
   Customer ODETTE ID (SFIDDEST): O0013VELBROOK7017
   Supplier gateway: oftp.quillmere.example (198.51.100.158)
   Customer gateway: oftp.velbrook.example (203.0.113.121)
   Protocol release level: 5 (OFTP 2.0)
   Data exchange buffer size (SSIDSDEB): 4096
   Credit (SSIDCRED): 64
   Buffer compression: no. Restart: yes. Secure authentication: no.
   File security and file compression: none (SFIDSEC 00, SFIDCOMP 0).
   Signed EERP: not required (SFIDSIGN N).
   The Customer returns an EERP for every virtual file it accepts.

2. Virtual files
   Invoices: one interchange per virtual file, dataset name (SFIDDSN) QUILLMERE.INVOIC.
   File format U. SFIDDATE and SFIDTIME are set by the Supplier's gateway to
   the date and time the virtual file is made available for transmission.

3. EDIFACT
   Syntax identifier and version (UNB S001): UNOA, version 3.
   Supplier interchange sender ID (UNB S002 0004 / 0007): QUILLMERE05 / ZZZ
   Customer interchange recipient ID (UNB S003 0010 / 0007): VELBROOK73 / ZZZ
   Both IDs are mutually defined between the parties by this agreement, so the
   identification code qualifier (0007) is ZZZ (mutually defined).
   Messages: INVOIC D.96A, one message per interchange.
   Interchanges are sent without line feeds between segments.
   The Customer's translator returns a CONTRL message for every rejected
   interchange, as a separate virtual file over the same OFTP2 link.

4. Support contacts
   Supplier EDI desk: Dana Brandt
   Customer EDI operations: Morgan Price

5. Supplier gateway set-up
   The Supplier runs two OFTP2 gateway nodes, gw1 and gw2, active-active. Both use
   the Supplier ODETTE ID and certificate above and take files from one shared
   outbound queue; either node may transmit any file.
```

## Document 2: OFTP2 gateway debug trace (sender side) (oftp2_session.log)

```text
# OFTP2 gateway debug trace, Quillmere Drivetrain Ltd (O0013QUILLMERE9940), node gw1
# '>>' = command exchange buffer sent by this gateway, '<<' = received from the
# remote OFTP2 location. Each buffer is shown as transmitted, between [ and ]
# (Stream Transmission Header omitted, non-printable octets as \xNN).
# '..' = gateway event, '!!' = gateway warning. Passwords are masked.
2026-10-30 06:11:23.000 S4035 .. session S4035: TCP connect to oftp.ostley.example (203.0.113.218), TLS 1.3 established
2026-10-30 06:11:23.159 S4035 << [IODETTE FTP READY \x0D]
2026-10-30 06:11:23.221 S4035 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 06:11:23.362 S4035 << [X5O0013OSTLEY2617          ********04096BNYN064N            \x0D]
2026-10-30 06:11:23.432 S4035 .. queued DESADV_OSTLEY_061005.edi
2026-10-30 06:11:23.491 S4035 >> [HQUILLMERE.DESADV             202610300610050001        O0013OSTLEY2617          O0013QUILLMERE9940       U000000000000000055000000000005500000000000000000000000N000]
2026-10-30 06:11:23.602 S4035 << [200000000000000000]
2026-10-30 06:11:23.979 S4035 .. DATA: 14 exchange buffer(s), 56134 octets
2026-10-30 06:11:24.000 S4035 >> [T0000000000000000000000000000056134]
2026-10-30 06:11:24.033 S4035 << [4N]
2026-10-30 06:11:24.177 S4035 .. file transferred, awaiting EERP
2026-10-30 06:11:24.229 S4035 >> [R]
2026-10-30 06:11:24.350 S4035 << [F00000\x0D]
2026-10-30 06:11:24.471 S4035 .. session closed
2026-10-30 06:41:03.000 S4025 .. session S4025: TCP connect to oftp.wrenmoor.example (203.0.113.95), TLS 1.3 established
2026-10-30 06:41:03.173 S4025 << [IODETTE FTP READY \x0D]
2026-10-30 06:41:03.314 S4025 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 06:41:03.393 S4025 << [X5O0013WRENMOOR9312        ********04096BNYN064N            \x0D]
2026-10-30 06:41:03.487 S4025 .. queued DESADV_WRENMOOR_064003.edi
2026-10-30 06:41:03.556 S4025 >> [HQUILLMERE.DESADV             202610300640030001        O0013WRENMOOR9312        O0013QUILLMERE9940       U000000000000000034000000000003400000000000000000000000N000]
2026-10-30 06:41:03.647 S4025 << [200000000000000000]
2026-10-30 06:41:03.809 S4025 .. DATA: 9 exchange buffer(s), 34337 octets
2026-10-30 06:41:03.877 S4025 >> [T0000000000000000000000000000034337]
2026-10-30 06:41:04.036 S4025 << [4N]
2026-10-30 06:41:04.123 S4025 .. file transferred, awaiting EERP
2026-10-30 06:41:04.190 S4025 >> [R]
2026-10-30 06:41:04.341 S4025 << [F00000\x0D]
2026-10-30 06:41:04.446 S4025 .. session closed
2026-10-30 06:47:41.471 S4036 .. session S4036: inbound TCP connection from 203.0.113.218, TLS 1.3 established
2026-10-30 06:47:41.601 S4036 >> [IODETTE FTP READY \x0D]
2026-10-30 06:47:41.629 S4036 << [X5O0013OSTLEY2617          ********04096BNYN064N            \x0D]
2026-10-30 06:47:41.652 S4036 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 06:47:41.711 S4036 << [EQUILLMERE.DESADV             202610300610050001        O0013QUILLMERE9940       O0013OSTLEY2617          \x00\x00\x00\x00]
2026-10-30 06:47:41.779 S4036 >> [P]
2026-10-30 06:47:41.868 S4036 .. EERP matched to DESADV_OSTLEY_061005.edi (sent 30 Oct 06:11): delivered
2026-10-30 06:47:41.937 S4036 << [R]
2026-10-30 06:47:41.970 S4036 >> [F00000\x0D]
2026-10-30 06:47:42.150 S4036 .. session closed
2026-10-30 07:03:09.000 S4023 .. session S4023: TCP connect to oftp.harrowfld.example (203.0.113.239), TLS 1.3 established
2026-10-30 07:03:09.131 S4023 << [IODETTE FTP READY \x0D]
2026-10-30 07:03:09.296 S4023 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 07:03:09.336 S4023 << [X5O0013HARROWFLD8198       ********04096BNYN064N            \x0D]
2026-10-30 07:03:09.417 S4023 .. queued DESADV_HARROWFLD_070216.edi
2026-10-30 07:03:09.578 S4023 >> [HQUILLMERE.DESADV             202610300702160001        O0013HARROWFLD8198       O0013QUILLMERE9940       U000000000000000020000000000002000000000000000000000000N000]
2026-10-30 07:03:09.748 S4023 << [200000000000000000]
2026-10-30 07:03:10.039 S4023 .. DATA: 5 exchange buffer(s), 20345 octets
2026-10-30 07:03:10.059 S4023 >> [T0000000000000000000000000000020345]
2026-10-30 07:03:10.074 S4023 << [4N]
2026-10-30 07:03:10.210 S4023 .. file transferred, awaiting EERP
2026-10-30 07:03:10.260 S4023 >> [R]
2026-10-30 07:03:10.370 S4023 << [F00000\x0D]
2026-10-30 07:03:10.489 S4023 .. session closed
2026-10-30 07:19:53.446 S4026 .. session S4026: inbound TCP connection from 203.0.113.95, TLS 1.3 established
2026-10-30 07:19:53.549 S4026 >> [IODETTE FTP READY \x0D]
2026-10-30 07:19:53.619 S4026 << [X5O0013WRENMOOR9312        ********04096BNYN064N            \x0D]
2026-10-30 07:19:53.782 S4026 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 07:19:53.960 S4026 << [EQUILLMERE.DESADV             202610300640030001        O0013QUILLMERE9940       O0013WRENMOOR9312        \x00\x00\x00\x00]
2026-10-30 07:19:54.094 S4026 >> [P]
2026-10-30 07:19:54.229 S4026 .. EERP matched to DESADV_WRENMOOR_064003.edi (sent 30 Oct 06:41): delivered
2026-10-30 07:19:54.368 S4026 << [HWRENMOOR.DELFOR              202610300719540001        O0013QUILLMERE9940       O0013WRENMOOR9312        U000000000000000013000000000001300000000000000000000000N000]
2026-10-30 07:19:54.388 S4026 >> [200000000000000000]
2026-10-30 07:19:54.566 S4026 .. DATA: 4 exchange buffer(s), 12612 octets
2026-10-30 07:19:54.583 S4026 << [T0000000000000000000000000000012612]
2026-10-30 07:19:54.699 S4026 >> [4N]
2026-10-30 07:19:54.818 S4026 .. stored as inbound/DELFOR_WRENMOOR_071954.edi
2026-10-30 07:19:54.870 S4026 << [R]
2026-10-30 07:19:54.895 S4026 >> [EWRENMOOR.DELFOR              202610300719540001        O0013WRENMOOR9312        O0013QUILLMERE9940       \x00\x00\x00\x00]
2026-10-30 07:19:55.043 S4026 << [P]
2026-10-30 07:19:55.221 S4026 >> [R]
2026-10-30 07:19:55.352 S4026 << [F00000\x0D]
2026-10-30 07:19:55.451 S4026 .. session closed
2026-10-30 07:22:48.000 S3918 .. session S3918: TCP connect to oftp.velbrook.example (203.0.113.121), TLS 1.3 established
2026-10-30 07:22:48.106 S3918 << [IODETTE FTP READY \x0D]
2026-10-30 07:22:48.155 S3918 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 07:22:48.253 S3918 << [X5O0013VELBROOK7017        ********04096BNYN064N            \x0D]
2026-10-30 07:22:48.272 S3918 .. queued INV58105.edi
2026-10-30 07:22:48.301 S3918 >> [HQUILLMERE.INVOIC             202610300722110001        O0013VELBROOK7017        O0013QUILLMERE9940       U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 07:22:48.389 S3918 << [200000000000000000]
2026-10-30 07:22:48.758 S3918 .. DATA: 1 exchange buffer(s), 336 octets
2026-10-30 07:22:48.857 S3918 >> [T0000000000000000000000000000000336]
2026-10-30 07:22:48.938 S3918 << [4N]
2026-10-30 07:22:48.998 S3918 .. file transferred, awaiting EERP
2026-10-30 07:22:49.124 S3918 >> [R]
2026-10-30 07:22:49.208 S3918 << [F00000\x0D]
2026-10-30 07:22:49.355 S3918 .. session closed
2026-10-30 07:38:33.000 S3919 .. session S3919: inbound TCP connection from 203.0.113.121, TLS 1.3 established
2026-10-30 07:38:33.157 S3919 >> [IODETTE FTP READY \x0D]
2026-10-30 07:38:33.240 S3919 << [X5O0013VELBROOK7017        ********04096BNYN064N            \x0D]
2026-10-30 07:38:33.252 S3919 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 07:38:33.386 S3919 << [EQUILLMERE.INVOIC             202610300722110001        O0013QUILLMERE9940       O0013VELBROOK7017        \x00\x00\x00\x00]
2026-10-30 07:38:33.564 S3919 >> [P]
2026-10-30 07:38:33.634 S3919 .. EERP matched to INV58105.edi: delivered
2026-10-30 07:38:33.657 S3919 << [R]
2026-10-30 07:38:33.820 S3919 >> [F00000\x0D]
2026-10-30 07:38:33.977 S3919 .. session closed
2026-10-30 07:49:52.489 S4024 .. session S4024: inbound TCP connection from 203.0.113.239, TLS 1.3 established
2026-10-30 07:49:52.664 S4024 >> [IODETTE FTP READY \x0D]
2026-10-30 07:49:52.827 S4024 << [X5O0013HARROWFLD8198       ********04096BNYN064N            \x0D]
2026-10-30 07:49:52.850 S4024 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 07:49:52.928 S4024 << [EQUILLMERE.DESADV             202610300702160001        O0013QUILLMERE9940       O0013HARROWFLD8198       \x00\x00\x00\x00]
2026-10-30 07:49:53.062 S4024 >> [P]
2026-10-30 07:49:53.142 S4024 .. EERP matched to DESADV_HARROWFLD_070216.edi (sent 30 Oct 07:03): delivered
2026-10-30 07:49:53.170 S4024 << [HHARROWFLD.DELJIT             202610300749530001        O0013QUILLMERE9940       O0013HARROWFLD8198       U000000000000000028000000000002800000000000000000000000N000]
2026-10-30 07:49:53.240 S4024 >> [200000000000000000]
2026-10-30 07:49:53.468 S4024 .. DATA: 7 exchange buffer(s), 28139 octets
2026-10-30 07:49:53.595 S4024 << [T0000000000000000000000000000028139]
2026-10-30 07:49:53.649 S4024 >> [4N]
2026-10-30 07:49:53.734 S4024 .. stored as inbound/DELJIT_HARROWFLD_074953.edi
2026-10-30 07:49:53.759 S4024 << [R]
2026-10-30 07:49:53.885 S4024 >> [EHARROWFLD.DELJIT             202610300749530001        O0013HARROWFLD8198       O0013QUILLMERE9940       \x00\x00\x00\x00]
2026-10-30 07:49:54.035 S4024 << [P]
2026-10-30 07:49:54.115 S4024 >> [R]
2026-10-30 07:49:54.205 S4024 << [F00000\x0D]
2026-10-30 07:49:54.330 S4024 .. session closed
2026-10-30 07:56:43.000 ----- .. outbound TCP connect to oftp.ostley.example (203.0.113.218) timed out after 30 s, retry in 120 s
2026-10-30 07:59:29.000 S4033 .. session S4033: TCP connect to oftp.ostley.example (203.0.113.218), TLS 1.3 established
2026-10-30 07:59:29.116 S4033 << [IODETTE FTP READY \x0D]
2026-10-30 07:59:29.262 S4033 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 07:59:29.363 S4033 << [X5O0013OSTLEY2617          ********04096BNYN064N            \x0D]
2026-10-30 07:59:29.436 S4033 .. queued INVOIC_OSTLEY_075619.edi
2026-10-30 07:59:29.452 S4033 >> [HQUILLMERE.INVOIC             202610300756190001        O0013OSTLEY2617          O0013QUILLMERE9940       U000000000000000005000000000000500000000000000000000000N000]
2026-10-30 07:59:29.565 S4033 << [200000000000000000]
2026-10-30 07:59:29.900 S4033 .. DATA: 2 exchange buffer(s), 4325 octets
2026-10-30 07:59:30.026 S4033 >> [T0000000000000000000000000000004325]
2026-10-30 07:59:30.154 S4033 << [4N]
2026-10-30 07:59:30.187 S4033 .. file transferred, awaiting EERP
2026-10-30 07:59:30.294 S4033 >> [R]
2026-10-30 07:59:30.322 S4033 << [F00000\x0D]
2026-10-30 07:59:30.333 S4033 .. session closed
2026-10-30 08:29:51.333 S4034 .. session S4034: inbound TCP connection from 203.0.113.218, TLS 1.3 established
2026-10-30 08:29:51.423 S4034 >> [IODETTE FTP READY \x0D]
2026-10-30 08:29:51.478 S4034 << [X5O0013OSTLEY2617          ********04096BNYN064N            \x0D]
2026-10-30 08:29:51.587 S4034 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 08:29:51.620 S4034 << [EQUILLMERE.INVOIC             202610300756190001        O0013QUILLMERE9940       O0013OSTLEY2617          \x00\x00\x00\x00]
2026-10-30 08:29:51.637 S4034 >> [P]
2026-10-30 08:29:51.692 S4034 .. EERP matched to INVOIC_OSTLEY_075619.edi (sent 30 Oct 07:59): delivered
2026-10-30 08:29:51.801 S4034 << [R]
2026-10-30 08:29:51.957 S4034 >> [F00000\x0D]
2026-10-30 08:29:52.135 S4034 .. session closed
2026-10-30 08:54:59.000 S4029 .. session S4029: TCP connect to oftp.wrenmoor.example (203.0.113.95), TLS 1.3 established
2026-10-30 08:54:59.117 S4029 << [IODETTE FTP READY \x0D]
2026-10-30 08:54:59.135 S4029 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 08:54:59.210 S4029 << [X5O0013WRENMOOR9312        ********04096BNYN064N            \x0D]
2026-10-30 08:54:59.223 S4029 .. queued DESADV_WRENMOOR_085351.edi
2026-10-30 08:54:59.372 S4029 >> [HQUILLMERE.DESADV             202610300853510001        O0013WRENMOOR9312        O0013QUILLMERE9940       U000000000000000048000000000004800000000000000000000000N000]
2026-10-30 08:54:59.547 S4029 << [200000000000000000]
2026-10-30 08:54:59.779 S4029 .. DATA: 12 exchange buffer(s), 48629 octets
2026-10-30 08:54:59.881 S4029 >> [T0000000000000000000000000000048629]
2026-10-30 08:54:59.930 S4029 << [4N]
2026-10-30 08:55:00.067 S4029 .. file transferred, awaiting EERP
2026-10-30 08:55:00.114 S4029 >> [R]
2026-10-30 08:55:00.260 S4029 << [F00000\x0D]
2026-10-30 08:55:00.332 S4029 .. session closed
2026-10-30 08:55:26.000 S4027 .. session S4027: TCP connect to oftp.wrenmoor.example (203.0.113.95), TLS 1.3 established
2026-10-30 08:55:26.055 S4027 << [IODETTE FTP READY \x0D]
2026-10-30 08:55:26.132 S4027 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 08:55:26.185 S4027 << [X5O0013WRENMOOR9312        ********04096BNYN064N            \x0D]
2026-10-30 08:55:26.319 S4027 .. queued INVOIC_WRENMOOR_085406.edi
2026-10-30 08:55:26.486 S4027 >> [HQUILLMERE.INVOIC             202610300854060001        O0013WRENMOOR9312        O0013QUILLMERE9940       U000000000000000055000000000005500000000000000000000000N000]
2026-10-30 08:55:26.504 S4027 << [200000000000000000]
2026-10-30 08:55:26.553 S4027 .. DATA: 14 exchange buffer(s), 56292 octets
2026-10-30 08:55:26.678 S4027 >> [T0000000000000000000000000000056292]
2026-10-30 08:55:26.702 S4027 << [4N]
2026-10-30 08:55:26.750 S4027 .. file transferred, awaiting EERP
2026-10-30 08:55:26.896 S4027 >> [R]
2026-10-30 08:55:27.070 S4027 << [F00000\x0D]
2026-10-30 08:55:27.170 S4027 .. session closed
2026-10-30 08:57:05.000 S4031 .. session S4031: TCP connect to oftp.thornvale.example (203.0.113.244), TLS 1.3 established
2026-10-30 08:57:05.118 S4031 << [IODETTE FTP READY \x0D]
2026-10-30 08:57:05.179 S4031 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 08:57:05.312 S4031 << [X5O0013THORNVALE5381       ********04096BNYN064N            \x0D]
2026-10-30 08:57:05.429 S4031 .. queued DESADV_THORNVALE_085645.edi
2026-10-30 08:57:05.529 S4031 >> [HQUILLMERE.DESADV             202610300856450001        O0013THORNVALE5381       O0013QUILLMERE9940       U000000000000000010000000000001000000000000000000000000N000]
2026-10-30 08:57:05.690 S4031 << [200000000000000000]
2026-10-30 08:57:05.758 S4031 .. DATA: 3 exchange buffer(s), 9343 octets
2026-10-30 08:57:05.813 S4031 >> [T0000000000000000000000000000009343]
2026-10-30 08:57:05.848 S4031 << [4N]
2026-10-30 08:57:06.013 S4031 .. file transferred, awaiting EERP
2026-10-30 08:57:06.139 S4031 >> [R]
2026-10-30 08:57:06.166 S4031 << [F00000\x0D]
2026-10-30 08:57:06.342 S4031 .. session closed
2026-10-30 08:59:09.000 ----- .. outbound TCP connect to oftp.harrowfld.example (203.0.113.239) timed out after 30 s, retry in 120 s
2026-10-30 09:01:55.000 S4019 .. session S4019: TCP connect to oftp.harrowfld.example (203.0.113.239), TLS 1.3 established
2026-10-30 09:01:55.179 S4019 << [IODETTE FTP READY \x0D]
2026-10-30 09:01:55.263 S4019 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 09:01:55.316 S4019 << [X5O0013HARROWFLD8198       ********04096BNYN064N            \x0D]
2026-10-30 09:01:55.462 S4019 .. queued DESADV_HARROWFLD_085807.edi
2026-10-30 09:01:55.615 S4019 >> [HQUILLMERE.DESADV             202610300858070001        O0013HARROWFLD8198       O0013QUILLMERE9940       U000000000000000046000000000004600000000000000000000000N000]
2026-10-30 09:01:55.784 S4019 << [200000000000000000]
2026-10-30 09:01:56.068 S4019 .. DATA: 12 exchange buffer(s), 47097 octets
2026-10-30 09:01:56.170 S4019 >> [T0000000000000000000000000000047097]
2026-10-30 09:01:56.189 S4019 << [4N]
2026-10-30 09:01:56.358 S4019 .. file transferred, awaiting EERP
2026-10-30 09:01:56.404 S4019 >> [R]
2026-10-30 09:01:56.536 S4019 << [F00000\x0D]
2026-10-30 09:01:56.548 S4019 .. session closed
2026-10-30 09:20:01.170 S4028 .. session S4028: inbound TCP connection from 203.0.113.95, TLS 1.3 established
2026-10-30 09:20:01.235 S4028 >> [IODETTE FTP READY \x0D]
2026-10-30 09:20:01.392 S4028 << [X5O0013WRENMOOR9312        ********04096BNYN064N            \x0D]
2026-10-30 09:20:01.520 S4028 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 09:20:01.611 S4028 << [EQUILLMERE.INVOIC             202610300854060001        O0013QUILLMERE9940       O0013WRENMOOR9312        \x00\x00\x00\x00]
2026-10-30 09:20:01.708 S4028 >> [P]
2026-10-30 09:20:01.752 S4028 .. EERP matched to INVOIC_WRENMOOR_085406.edi (sent 30 Oct 08:55): delivered
2026-10-30 09:20:01.875 S4028 << [HWRENMOOR.DELFOR              202610300920010001        O0013QUILLMERE9940       O0013WRENMOOR9312        U000000000000000002000000000000200000000000000000000000N000]
2026-10-30 09:20:01.907 S4028 >> [200000000000000000]
2026-10-30 09:20:02.217 S4028 .. DATA: 1 exchange buffer(s), 1669 octets
2026-10-30 09:20:02.285 S4028 << [T0000000000000000000000000000001669]
2026-10-30 09:20:02.395 S4028 >> [4N]
2026-10-30 09:20:02.561 S4028 .. stored as inbound/DELFOR_WRENMOOR_092001.edi
2026-10-30 09:20:02.693 S4028 << [R]
2026-10-30 09:20:02.863 S4028 >> [EWRENMOOR.DELFOR              202610300920010001        O0013WRENMOOR9312        O0013QUILLMERE9940       \x00\x00\x00\x00]
2026-10-30 09:20:02.936 S4028 << [P]
2026-10-30 09:20:03.001 S4028 >> [R]
2026-10-30 09:20:03.173 S4028 << [F00000\x0D]
2026-10-30 09:20:03.319 S4028 .. session closed
2026-10-30 09:22:13.000 ----- .. outbound TCP connect to oftp.harrowfld.example (203.0.113.239) timed out after 30 s, retry in 120 s
2026-10-30 09:25:09.000 S4021 .. session S4021: TCP connect to oftp.harrowfld.example (203.0.113.239), TLS 1.3 established
2026-10-30 09:25:09.136 S4021 << [IODETTE FTP READY \x0D]
2026-10-30 09:25:09.153 S4021 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 09:25:09.259 S4021 << [X5O0013HARROWFLD8198       ********04096BNYN064N            \x0D]
2026-10-30 09:25:09.414 S4021 .. queued DESADV_HARROWFLD_092100.edi
2026-10-30 09:25:09.475 S4021 >> [HQUILLMERE.DESADV             202610300921000001        O0013HARROWFLD8198       O0013QUILLMERE9940       U000000000000000049000000000004900000000000000000000000N000]
2026-10-30 09:25:09.531 S4021 << [200000000000000000]
2026-10-30 09:25:09.629 S4021 .. DATA: 13 exchange buffer(s), 49798 octets
2026-10-30 09:25:09.647 S4021 >> [T0000000000000000000000000000049798]
2026-10-30 09:25:09.803 S4021 << [4N]
2026-10-30 09:25:09.882 S4021 .. file transferred, awaiting EERP
2026-10-30 09:25:09.896 S4021 >> [R]
2026-10-30 09:25:10.002 S4021 << [F00000\x0D]
2026-10-30 09:25:10.182 S4021 .. session closed
2026-10-30 09:25:53.000 S3920 .. session S3920: TCP connect to oftp.velbrook.example (203.0.113.121), TLS 1.3 established
2026-10-30 09:25:53.069 S3920 << [IODETTE FTP READY \x0D]
2026-10-30 09:25:53.208 S3920 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 09:25:53.356 S3920 << [X5O0013VELBROOK7017        ********04096BNYN064N            \x0D]
2026-10-30 09:25:53.512 S3920 .. queued INV58106.edi
2026-10-30 09:25:53.681 S3920 >> [HQUILLMERE.INVOIC             202610300925060001        O0013VELBROOK7017        O0013QUILLMERE9940       U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 09:25:53.692 S3920 << [313N014DUPLICATE FILE]
2026-10-30 09:25:53.790 S3920 .. file refused by partner
2026-10-30 09:25:53.943 S3920 >> [R]
2026-10-30 09:25:53.958 S3920 << [F00000\x0D]
2026-10-30 09:25:54.074 S3920 .. session closed
2026-10-30 09:32:31.548 S4020 .. session S4020: inbound TCP connection from 203.0.113.239, TLS 1.3 established
2026-10-30 09:32:31.652 S4020 >> [IODETTE FTP READY \x0D]
2026-10-30 09:32:31.671 S4020 << [X5O0013HARROWFLD8198       ********04096BNYN064N            \x0D]
2026-10-30 09:32:31.722 S4020 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 09:32:31.783 S4020 << [EQUILLMERE.DESADV             202610300858070001        O0013QUILLMERE9940       O0013HARROWFLD8198       \x00\x00\x00\x00]
2026-10-30 09:32:31.957 S4020 >> [P]
2026-10-30 09:32:32.133 S4020 .. EERP matched to DESADV_HARROWFLD_085807.edi (sent 30 Oct 09:01): delivered
2026-10-30 09:32:32.267 S4020 << [R]
2026-10-30 09:32:32.431 S4020 >> [F00000\x0D]
2026-10-30 09:32:32.575 S4020 .. session closed
2026-10-30 09:52:03.332 S4030 .. session S4030: inbound TCP connection from 203.0.113.95, TLS 1.3 established
2026-10-30 09:52:03.431 S4030 >> [IODETTE FTP READY \x0D]
2026-10-30 09:52:03.440 S4030 << [X5O0013WRENMOOR9312        ********04096BNYN064N            \x0D]
2026-10-30 09:52:03.563 S4030 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 09:52:03.726 S4030 << [EQUILLMERE.DESADV             202610300853510001        O0013QUILLMERE9940       O0013WRENMOOR9312        \x00\x00\x00\x00]
2026-10-30 09:52:03.862 S4030 >> [P]
2026-10-30 09:52:03.997 S4030 .. EERP matched to DESADV_WRENMOOR_085351.edi (sent 30 Oct 08:54): delivered
2026-10-30 09:52:04.085 S4030 << [HWRENMOOR.DELJIT              202610300952030001        O0013QUILLMERE9940       O0013WRENMOOR9312        U000000000000000015000000000001500000000000000000000000N000]
2026-10-30 09:52:04.249 S4030 >> [200000000000000000]
2026-10-30 09:52:04.547 S4030 .. DATA: 4 exchange buffer(s), 14761 octets
2026-10-30 09:52:04.571 S4030 << [T0000000000000000000000000000014761]
2026-10-30 09:52:04.732 S4030 >> [4N]
2026-10-30 09:52:04.740 S4030 .. stored as inbound/DELJIT_WRENMOOR_095203.edi
2026-10-30 09:52:04.810 S4030 << [R]
2026-10-30 09:52:04.874 S4030 >> [EWRENMOOR.DELJIT              202610300952030001        O0013WRENMOOR9312        O0013QUILLMERE9940       \x00\x00\x00\x00]
2026-10-30 09:52:04.917 S4030 << [P]
2026-10-30 09:52:05.007 S4030 >> [R]
2026-10-30 09:52:05.138 S4030 << [F00000\x0D]
2026-10-30 09:52:05.278 S4030 .. session closed
2026-10-30 09:54:05.000 S3921 .. session S3921: TCP connect to oftp.velbrook.example (203.0.113.121), TLS 1.3 established
2026-10-30 09:54:05.056 S3921 << [IODETTE FTP READY \x0D]
2026-10-30 09:54:05.153 S3921 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 09:54:05.299 S3921 << [X5O0013VELBROOK7017        ********04096BNYN064N            \x0D]
2026-10-30 09:54:05.360 S3921 .. queued INV58106.edi (retry)
2026-10-30 09:54:05.474 S3921 >> [HQUILLMERE.INVOIC             202610300925060001        O0013VELBROOK7017        O0013QUILLMERE9940       U000000000000000001000000000000100000000000000000000000N000]
2026-10-30 09:54:05.567 S3921 << [313N014DUPLICATE FILE]
2026-10-30 09:54:05.684 S3921 .. file refused by partner
2026-10-30 09:54:05.760 S3921 >> [R]
2026-10-30 09:54:05.849 S3921 << [F00000\x0D]
2026-10-30 09:54:06.013 S3921 .. session closed
2026-10-30 10:02:30.182 S4022 .. session S4022: inbound TCP connection from 203.0.113.239, TLS 1.3 established
2026-10-30 10:02:30.351 S4022 >> [IODETTE FTP READY \x0D]
2026-10-30 10:02:30.359 S4022 << [X5O0013HARROWFLD8198       ********04096BNYN064N            \x0D]
2026-10-30 10:02:30.449 S4022 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 10:02:30.583 S4022 << [EQUILLMERE.DESADV             202610300921000001        O0013QUILLMERE9940       O0013HARROWFLD8198       \x00\x00\x00\x00]
2026-10-30 10:02:30.593 S4022 >> [P]
2026-10-30 10:02:30.601 S4022 .. EERP matched to DESADV_HARROWFLD_092100.edi (sent 30 Oct 09:25): delivered
2026-10-30 10:02:30.695 S4022 << [R]
2026-10-30 10:02:30.815 S4022 >> [F00000\x0D]
2026-10-30 10:02:30.989 S4022 .. session closed
2026-10-30 10:06:10.342 S4032 .. session S4032: inbound TCP connection from 203.0.113.244, TLS 1.3 established
2026-10-30 10:06:10.495 S4032 >> [IODETTE FTP READY \x0D]
2026-10-30 10:06:10.607 S4032 << [X5O0013THORNVALE5381       ********04096BNYN064N            \x0D]
2026-10-30 10:06:10.651 S4032 >> [X5O0013QUILLMERE9940       ********04096BNYN064N            \x0D]
2026-10-30 10:06:10.728 S4032 << [EQUILLMERE.DESADV             202610300856450001        O0013QUILLMERE9940       O0013THORNVALE5381       \x00\x00\x00\x00]
2026-10-30 10:06:10.896 S4032 >> [P]
2026-10-30 10:06:10.997 S4032 .. EERP matched to DESADV_THORNVALE_085645.edi (sent 30 Oct 08:57): delivered
2026-10-30 10:06:11.040 S4032 << [R]
2026-10-30 10:06:11.103 S4032 >> [F00000\x0D]
2026-10-30 10:06:11.139 S4032 .. session closed
```

## Document 3: EDIFACT interchange the ticket is about (as transmitted) (interchange.edi)

```text
UNB+UNOA:3+QUILLMERE05:ZZZ+VELBROOK73:ZZZ+261030:0925+058106'UNH+1+INVOIC:D:96A:UN'BGM+380+INV58106+9'DTM+137:20261030:102'NAD+SE+++QUILLMERE DRIVETRAIN LTD'NAD+BY+++VELBROOK VEHICLE ASSEMBLY'CUX+2:EUR:4'LIN+1++P-43772:IN'QTY+47:337'MOA+203:14079.86'PRI+AAA:41.78'LIN+2++P-05002:IN'QTY+47:356'MOA+203:761.84'PRI+AAA:2.14'UNS+S'MOA+77:17810.04'TAX+7+VAT+++:::20+S'MOA+124:2968.34'UNT+19+1'UNZ+1+058106'
```

## Document 4: Partner response (partner_response.txt)

```text
From: Morgan Price, EDI operations, Velbrook Vehicle Assembly
To: Dana Brandt, Quillmere Drivetrain Ltd
Subject: RE: duplicate file

Hello,

Our gateway refused the file as a duplicate. We have not changed anything on our side. Please check.

Regards,
Morgan Price
```

## Document 5: Specification extracts (spec_extracts.txt)

```text
RFC 5024 (ODETTE File Transfer Protocol 2), section 1.5.2. Verbatim extract.

1.5.2.  Identification

   Dataset Name

      Dataset name of the Virtual File being transferred, assigned by
      bilateral agreement.

   Time stamp (HHMMSScccc)

      A file qualifier indicating the time the Virtual File was made
      available for transmission.  The counter (cccc=0001-9999) gives
      higher resolution.

   Date stamp (CCYYMMDD)

      A file qualifier indicating the date the Virtual File was made
      available for transmission.

   The Dataset Name, Date, and Time attributes are assigned by the
   Virtual File's originator and are used to uniquely identify a file.
   They are all mandatory and must not be changed by intermediate
   locations.

   The User Monitor may use the Virtual File Date and Time attributes in
   local processes involving date comparisons and calculations.  Any
   such use falls outside the scope of this protocol.

RFC 5024 (ODETTE File Transfer Protocol 2), section 5.3.3. Verbatim extract.

5.3.3.  SFID - Start File

   o-------------------------------------------------------------------o
   |       SFID        Start File                                      |
   |                                                                   |
   |       Start File Phase           Speaker ----> Listener           |
   |-------------------------------------------------------------------|
   | Pos | Field     | Description                           | Format  |
   |-----+-----------+---------------------------------------+---------|
   |   0 | SFIDCMD   | SFID Command, 'H'                     | F X(1)  |
   |   1 | SFIDDSN   | Virtual File Dataset Name             | V X(26) |
   |  27 | SFIDRSV1  | Reserved                              | F X(3)  |
   |  30 | SFIDDATE  | Virtual File Date stamp, (CCYYMMDD)   | V 9(8)  |
   |  38 | SFIDTIME  | Virtual File Time stamp, (HHMMSScccc) | V 9(10) |
   |  48 | SFIDUSER  | User Data                             | V X(8)  |
   |  56 | SFIDDEST  | Destination                           | V X(25) |
   |  81 | SFIDORIG  | Originator                            | V X(25) |
   | 106 | SFIDFMT   | File Format (F/V/U/T)                 | F X(1)  |
   | 107 | SFIDLRECL | Maximum Record Size                   | V 9(5)  |
   | 112 | SFIDFSIZ  | File Size, 1K blocks                  | V 9(13) |
   | 125 | SFIDOSIZ  | Original File Size, 1K blocks         | V 9(13) |
   | 138 | SFIDREST  | Restart Position                      | V 9(17) |
   | 155 | SFIDSEC   | Security Level                        | F 9(2)  |
   | 157 | SFIDCIPH  | Cipher suite selection                | F 9(2)  |
   | 159 | SFIDCOMP  | File compression algorithm            | F 9(1)  |
   | 160 | SFIDENV   | File enveloping format                | F 9(1)  |
   | 161 | SFIDSIGN  | Signed EERP request                   | F X(1)  |
   | 162 | SFIDDESCL | Virtual File Description length       | V 9(3)  |
   | 165 | SFIDDESC  | Virtual File Description              | V T(n)  |
   o-------------------------------------------------------------------o

   SFIDCMD   Command Code                                      Character

      Value: 'H'  SFID Command identifier.

   SFIDDSN   Virtual File Dataset Name                        String(26)

             Dataset name of the Virtual File being transferred,
             assigned by bilateral agreement.

             No general structure is defined for this attribute.

             See Virtual Files - Identification (Section 1.5.2)

   SFIDRSV1  Reserved                                          String(3)

             This field is reserved for future use.

   SFIDDATE  Virtual File Date stamp                          Numeric(8)

     Format: 'CCYYMMDD'  8 decimal digits representing the century,
             year, month, and day.

             Date stamp assigned by the Virtual File's Originator
             indicating when the file was made available for
             transmission.

             See Virtual Files - Identification (Section 1.5.2)

   SFIDTIME  Virtual File Time stamp                         Numeric(10)

     Format: 'HHMMSScccc'  10 decimal digits representing hours,
             minutes, seconds, and a counter (0001-9999), which gives
             higher resolution.

             Time stamp assigned by the Virtual File's Originator
             indicating when the file was made available for
             transmission.

             See Virtual Files - Identification (Section 1.5.2)

   SFIDUSER  User Data                                         String(8)

             May be used by ODETTE-FTP in any way.  If unused, it should
             be initialised to spaces.  It is expected that a bilateral
             agreement exists as to the meaning of the data.

   SFIDDEST  Destination                                      String(25)

     Format: See Identification Code (Section 5.4)

             The Final Recipient of the Virtual File.

             This is the location that will look into the Virtual File
             content and perform mapping functions.  It is also the
             location that creates the End to End Response (EERP)
             command for the received file.

   SFIDORIG  Originator                                       String(25)

     Format: See Identification Code (Section 5.4)

             Originator of the Virtual File.

             It is the location that created (mapped) the data for
             transmission.

   SFIDFMT   File Format                                       Character

      Value: 'F'  Fixed format binary file
             'V'  Variable format binary file
             'U'  Unstructured binary file
             'T'  Text

             Virtual File format.  Used to calculate the restart
             position (Section 1.5.4).

             Once a file has been signed, compressed, and/or encrypted,
             in file format terms it becomes unstructured, format U.
             The record boundaries are no longer discernable until the
             file is decrypted, decompressed, and/or verified.  SFID
             File Format Field in this scenario indicates the format of
             the original file, and the transmitted file must be treated
             as U format.

   SFIDLRECL Maximum Record Size                              Numeric(5)

    Maximum: 99999

             Length in octets of the longest logical record that may be
             transferred to a location.  Only user data is included.

             If SFIDFMT is 'T' or 'U', then this attribute must be set
             to '00000'.

             If SFIDFMT is 'V' and the file is compressed, encrypted, or
             signed, then the maximum value of SFIDRECL is '65536'.

   SFIDFSIZ  Transmitted File Size                           Numeric(13)

    Maximum: 9999999999999

             Space in 1K (1024 octet) blocks required at the Originator
             location to store the actual Virtual File that is to be
             transmitted.

             For example, if a file is compressed before sending, then
             this is the space required to store the compressed file.

             This parameter is intended to provide only a good estimate
             of the Virtual File size.

             Using 13 digits allows for a maximum file size of
             approximately 9.3 PB (petabytes) to be transmitted.

   SFIDOSIZ  Original File Size                              Numeric(13)

    Maximum: 9999999999999

             Space in 1K (1024 octet) blocks required at the Originator
             location to store the original before it was signed,
             compressed, and/or encrypted.

             If no security or compression services have been used,
             SFIDOSIZ should contain the same value as SFIDFSIZ.

             If the original file size is not known, the value zero
             should be used.

             This parameter is intended to provide only a good estimate
             of the original file size.

             The sequence of events in file exchange are:

              (a) raw data file ready to be sent
                   SFIDOSIZ = Original File Size

              (b) signing/compression/encryption

              (c) transmission
                   SFIDFSIZ = Transmitted File Size

              (d) decryption/decompression/verification

              (e) received raw data file for in-house applications
                   SFIDOSIZ = Original File Size

             The Transmitted File Size at (c) indicates to the receiver
             how much storage space is needed to receive the file.

             The Original File Size at (e) indicates to the in-house
             application how much storage space is needed to process the
             file.

   SFIDREST  Restart Position                                Numeric(17)

    Maximum: 99999999999999999

             Virtual File restart position.

             The count represents the:
                - Record Number if SSIDFMT is 'F' or 'V'.
                - File offset in 1K (1024 octet) blocks if SFIDFMT is
                  'U' or 'T'.

             The count will express the transmitted user data (i.e.,
             before ODETTE-FTP buffer compression, header not included).

             After negotiation between adjacent locations,
             retransmission will start at the lowest value.

             Once a file has been signed, compressed, and/or encrypted,
             in file format terms, it has become unstructured, like
             format U.  The file should be treated as format U for the
             purposes of restart, regardless of the actual value in
             SFIDFMT.

   SFIDSEC   Security Level                                   Numeric(2)

      Value: '00'  No security services
             '01'  Encrypted
             '02'  Signed
             '03'  Encrypted and signed

             Indicates whether the file has been signed and/or encrypted
             before transmission. (See Section 6.2.)

   SFIDCIPH  Cipher suite selection                           Numeric(2)

      Value: '00'  No security services
             '01'  See Section 10.2

             Indicates the cipher suite used to sign and/or encrypt the
             file and also to indicate the cipher suite that should be
             used when a signed EERP or NERP is requested.

   SFIDCOMP  File compression algorithm                       Numeric(1)

      Value: '0'  No compression
             '1'  Compressed with [ZLIB] algorithm

             Indicates the algorithm used to compress the file.
             (See Section 6.4.)

   SFIDENV   File enveloping format                           Numeric(1)

      Value: '0'  No envelope
             '1'  File is enveloped using [CMS]

             Indicates the enveloping format used in the file.

             If the file is encrypted/signed/compressed or is an
             enveloped file for the exchange and revocation of
             certificates, this field must be set accordingly.

   SFIDSIGN  Signed EERP request                               Character

      Value: 'Y'  The EERP returned in acknowledgement of the file
                  must be signed
             'N'  The EERP must not be signed

             Requests whether the EERP returned for the file must be
             signed.

   SFIDDESCL Virtual File Description length                  Numeric(3)

             Length in octets of the field SFIDDESC.

             A value of 0 indicates that no description is present.

   SFIDDESC  Virtual File Description                         [UTF-8](n)

             May be used by ODETTE-FTP in any way.  If not used,
             SFIDDESCL should be set to zero.

             No general structure is defined for this attribute, but it
             is expected that a bilateral agreement exists as to the
             meaning of the data.

             It is encoded using [UTF-8] to support a range of national
             languages.

             Maximum length of the encoded value is 999 octets.

RFC 5024 (ODETTE File Transfer Protocol 2), section 5.3.5. Verbatim extract.

5.3.5.  SFNA - Start File Negative Answer

   o-------------------------------------------------------------------o
   |       SFNA        Start File Negative Answer                      |
   |                                                                   |
   |       Start File Phase           Speaker <---- Listener           |
   |-------------------------------------------------------------------|
   | Pos | Field     | Description                           | Format  |
   |-----+-----------+---------------------------------------+---------|
   |   0 | SFNACMD   | SFNA Command, '3'                     | F X(1)  |
   |   1 | SFNAREAS  | Answer Reason                         | F 9(2)  |
   |   3 | SFNARRTR  | Retry Indicator, (Y/N)                | F X(1)  |
   |   4 | SFNAREASL | Answer Reason Text Length             | V 9(3)  |
   |   7 | SFNAREAST | Answer Reason Text                    | V T(n)  |
   o-------------------------------------------------------------------o

   SFNACMD   Command Code                                      Character

      Value: '3'  SFNA Command identifier.

   SFNAREAS  Answer Reason                                    Numeric(2)

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
             '99'  Unspecified reason.

             Reason why transmission cannot proceed.

   SFNARRTR  Retry Indicator                                   Character

      Value: 'N'  Transmission should not be retried.
             'Y'  The transmission may be retried later.

             This parameter is used to advise the Speaker if it should
             retry at a later time due to a temporary condition at the
             Listener site, such as a lack of storage space.  It should
             be used in conjunction with the Answer Reason code
             (SFNAREAS).

             An invalid file name error code may be the consequence of a
             problem in the mapping of the Virtual File on to a real
             file.  Such problems cannot always be resolved immediately.
             It is therefore recommended that when an SFNA with Retry =
             Y is received the User Monitor attempts to retransmit the
             relevant file in a subsequent session.

   SFNAREASL Answer Reason Text Length                        Numeric(3)

             Length in octets of the field SFNAREAST.

             0 indicates that no SFNAREAST field follows.

   SFNAREAST Answer Reason Text                               [UTF-8](n)

             Reason why transmission cannot proceed in plain text.

             It is encoded using [UTF-8].

             Maximum length of the encoded reason is 999 octets.

             No general structure is defined for this attribute.
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

value: a JSON string holding the SFIDTIME of the virtual file the receiver refused.

Example of the format only (not a hint):
```json
{"cause": "file_too_large", "layer": "transport", "owner": "receiver", "location": ["SFID.SFIDFSIZ"], "next_check": "none", "value": "12345"}
```
