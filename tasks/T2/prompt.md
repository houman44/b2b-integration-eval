# Ticket T2

You work on the EDI support desk that serves the sender of the file described
below. A customer has raised the ticket that follows. The partner agreement,
the sender's OFTP2 gateway trace (and, where available, its file status report),
the EDIFACT interchange in question, the partner's response and extracts from the
specifications are attached. Everything you need
is in these documents. All companies, identifiers and documents are synthetic.

## The ticket

```text
From: Jordan Tanaka, EDI desk, Fenwray Castings Ltd
Subject: restarted transfers to Marrowgate Motor Works always fail

Our nightly invoice batch to Marrowgate Motor Works is about 48 MB. Whenever the line drops during the night and our gateway restarts the transfer, Marrowgate Motor Works refuses the file at the end with 'BYTE COUNT MISMATCH'. When we send the whole file again from the start it always goes through. It happened again last night: the same line drop also interrupted our nightly DESADV batch to Ostley Fasteners, and that one restarted and was delivered without a problem, so our gateway's restart works. Restart is switched on in the agreement, so Marrowgate Motor Works's restart support must be broken. Please find the root cause and tell us who has to fix it.
```

## Document 1: Partner agreement (partner_agreement.txt)

```text
PARTNER AGREEMENT: ELECTRONIC DATA INTERCHANGE
Between Fenwray Castings Ltd (the Supplier) and Marrowgate Motor Works (the Customer)
Effective 1 March 2026. Synthetic document written for this evaluation.

1. Transport: OFTP2 (RFC 5024) over TCP/IP with TLS
   Supplier ODETTE ID (SFIDORIG): O0013FENWRAY3004
   Customer ODETTE ID (SFIDDEST): O0013MARROWGATE1395
   Supplier gateway: oftp.fenwray.example (198.51.100.246)
   Customer gateway: oftp.marrowgate.example (203.0.113.143)
   Protocol release level: 5 (OFTP 2.0)
   Data exchange buffer size (SSIDSDEB): 4096
   Credit (SSIDCRED): 64
   Buffer compression: no. Restart: yes. Secure authentication: no.
   File security and file compression: none (SFIDSEC 00, SFIDCOMP 0).
   Signed EERP: not required (SFIDSIGN N).
   The Customer returns an EERP for every virtual file it accepts.

2. Virtual files
   Invoices: nightly batch, one interchange per virtual file, dataset name (SFIDDSN) FENWRAY.INVBATCH.
   File format U. SFIDDATE and SFIDTIME are set by the Supplier's gateway to
   the date and time the virtual file is made available for transmission.

3. EDIFACT
   Syntax identifier and version (UNB S001): UNOA, version 3.
   Supplier interchange sender ID (UNB S002 0004 / 0007): FENWRAY89 / ZZZ
   Customer interchange recipient ID (UNB S003 0010 / 0007): MARROWGATE28 / ZZZ
   Both IDs are mutually defined between the parties by this agreement, so the
   identification code qualifier (0007) is ZZZ (mutually defined).
   Messages: INVOIC D.96A, up to 50000 messages per interchange.
   Interchanges are sent without line feeds between segments.
   The Customer's translator returns a CONTRL message for every rejected
   interchange, as a separate virtual file over the same OFTP2 link.

4. Support contacts
   Supplier EDI desk: Jordan Tanaka
   Customer EDI operations: Kim Price
```

## Document 2: OFTP2 gateway debug trace (sender side) (oftp2_session.log)

```text
# OFTP2 gateway debug trace, Fenwray Castings Ltd (O0013FENWRAY3004)
# '>>' = command exchange buffer sent by this gateway, '<<' = received from the
# remote OFTP2 location. Each buffer is shown as transmitted, between [ and ]
# (Stream Transmission Header omitted, non-printable octets as \xNN).
# '..' = gateway event, '!!' = gateway warning. Passwords are masked.
2026-10-30 02:11:28.000 S2792 .. session S2792: TCP connect to oftp.marrowgate.example (203.0.113.143), TLS 1.3 established
2026-10-30 02:11:28.126 S2792 << [IODETTE FTP READY \x0D]
2026-10-30 02:11:28.179 S2792 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 02:11:28.201 S2792 << [X5O0013MARROWGATE1395      ********04096BNYN064N            \x0D]
2026-10-30 02:11:28.337 S2792 .. queued INVOICES_20261030_NIGHT.edi
2026-10-30 02:11:28.472 S2792 >> [HFENWRAY.INVBATCH             202610300210500001        O0013MARROWGATE1395      O0013FENWRAY3004         U000000000000049152000000004915200000000000000000000000N000]
2026-10-30 02:11:28.580 S2792 << [200000000000000000]
2026-10-30 02:11:28.709 S2792 .. DATA: transfer started, 50331648 octets to send, credit window 64
2026-10-30 02:12:26.000 S2842 .. session S2842: TCP connect to oftp.ostley.example (203.0.113.26), TLS 1.3 established
2026-10-30 02:12:26.092 S2842 << [IODETTE FTP READY \x0D]
2026-10-30 02:12:26.158 S2842 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 02:12:26.334 S2842 << [X5O0013OSTLEY4641          ********04096BNYN064N            \x0D]
2026-10-30 02:12:26.463 S2842 .. queued DESADV_OSTLEY_20261030_NIGHT.edi
2026-10-30 02:12:26.570 S2842 >> [HFENWRAY.DESADVB              202610300212050001        O0013OSTLEY4641          O0013FENWRAY3004         V020000000000026793000000002679300000000000000000000000N000]
2026-10-30 02:12:26.666 S2842 << [200000000000000000]
2026-10-30 02:12:26.814 S2842 .. DATA: transfer started, 18157 records to send, credit window 64
2026-10-30 02:17:37.709 S2792 .. DATA: 33554432 octets sent, CDT received for every credit window
2026-10-30 02:17:37.709 S2792 !! TCP connection reset by peer
2026-10-30 02:17:37.709 S2842 .. DATA: 7163 records sent, CDT received for every credit window
2026-10-30 02:17:37.709 S2842 !! TCP connection reset by peer
2026-10-30 02:17:37.725 S2792 .. session aborted, file incomplete, restart position saved: 33554432
2026-10-30 02:17:37.868 S2842 .. session aborted, file incomplete, restart position saved: 7163
2026-10-30 02:20:26.725 S2793 .. session S2793: TCP connect to oftp.marrowgate.example (203.0.113.143), TLS 1.3 established
2026-10-30 02:20:26.868 S2793 << [IODETTE FTP READY \x0D]
2026-10-30 02:20:27.013 S2793 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 02:20:27.109 S2793 << [X5O0013MARROWGATE1395      ********04096BNYN064N            \x0D]
2026-10-30 02:20:27.138 S2793 .. restarting interrupted file
2026-10-30 02:20:27.193 S2793 >> [HFENWRAY.INVBATCH             202610300210500001        O0013MARROWGATE1395      O0013FENWRAY3004         U000000000000049152000000004915200000000033554432000000N000]
2026-10-30 02:20:27.273 S2793 << [200000000000032768]
2026-10-30 02:20:27.409 S2793 .. restart accepted by partner, sending remaining 50298880 octets
2026-10-30 02:21:00.709 S2843 .. session S2843: TCP connect to oftp.ostley.example (203.0.113.26), TLS 1.3 established
2026-10-30 02:21:00.859 S2843 << [IODETTE FTP READY \x0D]
2026-10-30 02:21:00.986 S2843 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 02:21:01.083 S2843 << [X5O0013OSTLEY4641          ********04096BNYN064N            \x0D]
2026-10-30 02:21:01.102 S2843 .. restarting interrupted file
2026-10-30 02:21:01.222 S2843 >> [HFENWRAY.DESADVB              202610300212050001        O0013OSTLEY4641          O0013FENWRAY3004         V020000000000026793000000002679300000000000007163000000N000]
2026-10-30 02:21:01.311 S2843 << [200000000000007163]
2026-10-30 02:21:01.451 S2843 .. restart accepted by partner, sending remaining 10994 records
2026-10-30 02:24:39.451 S2843 .. DATA: 10994 records sent
2026-10-30 02:24:39.580 S2843 >> [T0000000000001815700000000027435227]
2026-10-30 02:24:39.603 S2843 << [4N]
2026-10-30 02:24:39.720 S2843 .. file transferred, awaiting EERP
2026-10-30 02:24:39.792 S2843 >> [R]
2026-10-30 02:24:39.965 S2843 << [F00000\x0D]
2026-10-30 02:24:40.133 S2843 .. session closed
2026-10-30 02:28:22.409 S2793 .. DATA: 50298880 octets sent
2026-10-30 02:28:22.444 S2793 >> [T0000000000000000000000000050331648]
2026-10-30 02:28:22.545 S2793 << [511019BYTE COUNT MISMATCH]
2026-10-30 02:28:22.600 S2793 .. file refused by partner at end of file
2026-10-30 02:28:22.776 S2793 >> [R]
2026-10-30 02:28:22.843 S2793 << [F00000\x0D]
2026-10-30 02:28:22.969 S2793 .. session closed
2026-10-30 03:02:06.133 S2844 .. session S2844: inbound TCP connection from 203.0.113.26, TLS 1.3 established
2026-10-30 03:02:06.211 S2844 >> [IODETTE FTP READY \x0D]
2026-10-30 03:02:06.349 S2844 << [X5O0013OSTLEY4641          ********04096BNYN064N            \x0D]
2026-10-30 03:02:06.367 S2844 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 03:02:06.487 S2844 << [EFENWRAY.DESADVB              202610300212050001        O0013FENWRAY3004         O0013OSTLEY4641          \x00\x00\x00\x00]
2026-10-30 03:02:06.571 S2844 >> [P]
2026-10-30 03:02:06.689 S2844 .. EERP matched to DESADV_OSTLEY_20261030_NIGHT.edi: delivered
2026-10-30 03:02:06.813 S2844 << [R]
2026-10-30 03:02:06.885 S2844 >> [F00000\x0D]
2026-10-30 03:02:06.913 S2844 .. session closed
2026-10-30 05:04:55.000 S2905 .. session S2905: TCP connect to oftp.pemberline.example (203.0.113.108), TLS 1.3 established
2026-10-30 05:04:55.013 S2905 << [IODETTE FTP READY \x0D]
2026-10-30 05:04:55.147 S2905 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 05:04:55.232 S2905 << [X5O0013PEMBERLINE8594      ********04096BNYN064N            \x0D]
2026-10-30 05:04:55.374 S2905 .. queued DESADV_PEMBERLINE_050335.edi
2026-10-30 05:04:55.508 S2905 >> [HFENWRAY.DESADV               202610300503350001        O0013PEMBERLINE8594      O0013FENWRAY3004         U000000000000000042000000000004200000000000000000000000N000]
2026-10-30 05:04:55.541 S2905 << [200000000000000000]
2026-10-30 05:04:55.871 S2905 .. DATA: 11 exchange buffer(s), 42774 octets
2026-10-30 05:04:56.021 S2905 >> [T0000000000000000000000000000042774]
2026-10-30 05:04:56.039 S2905 << [4N]
2026-10-30 05:04:56.059 S2905 .. file transferred, awaiting EERP
2026-10-30 05:04:56.208 S2905 >> [R]
2026-10-30 05:04:56.295 S2905 << [F00000\x0D]
2026-10-30 05:04:56.472 S2905 .. session closed
2026-10-30 05:49:07.472 S2906 .. session S2906: inbound TCP connection from 203.0.113.108, TLS 1.3 established
2026-10-30 05:49:07.542 S2906 >> [IODETTE FTP READY \x0D]
2026-10-30 05:49:07.608 S2906 << [X5O0013PEMBERLINE8594      ********04096BNYN064N            \x0D]
2026-10-30 05:49:07.759 S2906 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 05:49:07.818 S2906 << [EFENWRAY.DESADV               202610300503350001        O0013FENWRAY3004         O0013PEMBERLINE8594      \x00\x00\x00\x00]
2026-10-30 05:49:07.923 S2906 >> [P]
2026-10-30 05:49:08.019 S2906 .. EERP matched to DESADV_PEMBERLINE_050335.edi (sent 30 Oct 05:04): delivered
2026-10-30 05:49:08.073 S2906 << [R]
2026-10-30 05:49:08.104 S2906 >> [F00000\x0D]
2026-10-30 05:49:08.209 S2906 .. session closed
2026-10-30 05:58:53.000 S2907 .. session S2907: TCP connect to oftp.calderbank.example (203.0.113.141), TLS 1.3 established
2026-10-30 05:58:53.058 S2907 << [IODETTE FTP READY \x0D]
2026-10-30 05:58:53.200 S2907 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 05:58:53.230 S2907 << [X5O0013CALDERBANK4600      ********04096BNYN064N            \x0D]
2026-10-30 05:58:53.360 S2907 .. queued DESADV_CALDERBANK_055802.edi
2026-10-30 05:58:53.533 S2907 >> [HFENWRAY.DESADV               202610300558020001        O0013CALDERBANK4600      O0013FENWRAY3004         U000000000000000054000000000005400000000000000000000000N000]
2026-10-30 05:58:53.671 S2907 << [200000000000000000]
2026-10-30 05:58:53.736 S2907 .. DATA: 14 exchange buffer(s), 54709 octets
2026-10-30 05:58:53.862 S2907 >> [T0000000000000000000000000000054709]
2026-10-30 05:58:53.890 S2907 << [4N]
2026-10-30 05:58:54.039 S2907 .. file transferred, awaiting EERP
2026-10-30 05:58:54.174 S2907 >> [R]
2026-10-30 05:58:54.232 S2907 << [F00000\x0D]
2026-10-30 05:58:54.353 S2907 .. session closed
2026-10-30 06:09:53.000 S2794 .. session S2794: TCP connect to oftp.marrowgate.example (203.0.113.143), TLS 1.3 established
2026-10-30 06:09:53.033 S2794 << [IODETTE FTP READY \x0D]
2026-10-30 06:09:53.053 S2794 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 06:09:53.074 S2794 << [X5O0013MARROWGATE1395      ********04096BNYN064N            \x0D]
2026-10-30 06:09:53.193 S2794 .. queued INVOICES_20261030_NIGHT.edi (manual resend)
2026-10-30 06:09:53.227 S2794 >> [HFENWRAY.INVBATCH             202610300608370001        O0013MARROWGATE1395      O0013FENWRAY3004         U000000000000049152000000004915200000000000000000000000N000]
2026-10-30 06:09:53.345 S2794 << [200000000000000000]
2026-10-30 06:17:22.000 S2895 .. session S2895: TCP connect to oftp.harrowfld.example (203.0.113.153), TLS 1.3 established
2026-10-30 06:17:22.066 S2895 << [IODETTE FTP READY \x0D]
2026-10-30 06:17:22.152 S2895 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 06:17:22.224 S2895 << [X5O0013HARROWFLD6335       ********04096BNYN064N            \x0D]
2026-10-30 06:17:22.340 S2895 .. queued DESADV_HARROWFLD_061602.edi
2026-10-30 06:17:22.436 S2895 >> [HFENWRAY.DESADV               202610300616020001        O0013HARROWFLD6335       O0013FENWRAY3004         U000000000000000038000000000003800000000000000000000000N000]
2026-10-30 06:17:22.535 S2895 << [200000000000000000]
2026-10-30 06:17:22.664 S2895 .. DATA: 10 exchange buffer(s), 38688 octets
2026-10-30 06:17:22.687 S2895 >> [T0000000000000000000000000000038688]
2026-10-30 06:17:22.787 S2895 << [4N]
2026-10-30 06:17:22.840 S2895 .. file transferred, awaiting EERP
2026-10-30 06:17:22.983 S2895 >> [R]
2026-10-30 06:17:23.078 S2895 << [F00000\x0D]
2026-10-30 06:17:23.243 S2895 .. session closed
2026-10-30 06:22:00.345 S2794 .. DATA: 50331648 octets sent
2026-10-30 06:22:00.511 S2794 >> [T0000000000000000000000000050331648]
2026-10-30 06:22:00.636 S2794 << [4N]
2026-10-30 06:22:00.661 S2794 .. file transferred, awaiting EERP
2026-10-30 06:22:00.745 S2794 >> [R]
2026-10-30 06:22:00.790 S2794 << [F00000\x0D]
2026-10-30 06:22:00.895 S2794 .. session closed
2026-10-30 06:24:52.353 S2908 .. session S2908: inbound TCP connection from 203.0.113.141, TLS 1.3 established
2026-10-30 06:24:52.522 S2908 >> [IODETTE FTP READY \x0D]
2026-10-30 06:24:52.593 S2908 << [X5O0013CALDERBANK4600      ********04096BNYN064N            \x0D]
2026-10-30 06:24:52.757 S2908 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 06:24:52.929 S2908 << [EFENWRAY.DESADV               202610300558020001        O0013FENWRAY3004         O0013CALDERBANK4600      \x00\x00\x00\x00]
2026-10-30 06:24:52.966 S2908 >> [P]
2026-10-30 06:24:53.014 S2908 .. EERP matched to DESADV_CALDERBANK_055802.edi (sent 30 Oct 05:58): delivered
2026-10-30 06:24:53.127 S2908 << [R]
2026-10-30 06:24:53.222 S2908 >> [F00000\x0D]
2026-10-30 06:24:53.342 S2908 .. session closed
2026-10-30 06:55:56.895 S2795 .. session S2795: inbound TCP connection from 203.0.113.143, TLS 1.3 established
2026-10-30 06:55:56.923 S2795 >> [IODETTE FTP READY \x0D]
2026-10-30 06:55:57.069 S2795 << [X5O0013MARROWGATE1395      ********04096BNYN064N            \x0D]
2026-10-30 06:55:57.150 S2795 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 06:55:57.192 S2795 << [EFENWRAY.INVBATCH             202610300608370001        O0013FENWRAY3004         O0013MARROWGATE1395      \x00\x00\x00\x00]
2026-10-30 06:55:57.222 S2795 >> [P]
2026-10-30 06:55:57.242 S2795 .. EERP matched to INVOICES_20261030_NIGHT.edi (manual resend): delivered
2026-10-30 06:55:57.268 S2795 << [R]
2026-10-30 06:55:57.357 S2795 >> [F00000\x0D]
2026-10-30 06:55:57.533 S2795 .. session closed
2026-10-30 07:00:21.000 S2897 .. session S2897: TCP connect to oftp.thornvale.example (203.0.113.133), TLS 1.3 established
2026-10-30 07:00:21.018 S2897 << [IODETTE FTP READY \x0D]
2026-10-30 07:00:21.152 S2897 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 07:00:21.322 S2897 << [X5O0013THORNVALE2316       ********04096BNYN064N            \x0D]
2026-10-30 07:00:21.456 S2897 .. queued DESADV_THORNVALE_065930.edi
2026-10-30 07:00:21.494 S2897 >> [HFENWRAY.DESADV               202610300659300001        O0013THORNVALE2316       O0013FENWRAY3004         U000000000000000045000000000004500000000000000000000000N000]
2026-10-30 07:00:21.617 S2897 << [200000000000000000]
2026-10-30 07:00:22.015 S2897 .. DATA: 12 exchange buffer(s), 46077 octets
2026-10-30 07:00:22.174 S2897 >> [T0000000000000000000000000000046077]
2026-10-30 07:00:22.224 S2897 << [4N]
2026-10-30 07:00:22.262 S2897 .. file transferred, awaiting EERP
2026-10-30 07:00:22.299 S2897 >> [R]
2026-10-30 07:00:22.435 S2897 << [F00000\x0D]
2026-10-30 07:00:22.561 S2897 .. session closed
2026-10-30 07:15:49.243 S2896 .. session S2896: inbound TCP connection from 203.0.113.153, TLS 1.3 established
2026-10-30 07:15:49.396 S2896 >> [IODETTE FTP READY \x0D]
2026-10-30 07:15:49.570 S2896 << [X5O0013HARROWFLD6335       ********04096BNYN064N            \x0D]
2026-10-30 07:15:49.598 S2896 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 07:15:49.633 S2896 << [EFENWRAY.DESADV               202610300616020001        O0013FENWRAY3004         O0013HARROWFLD6335       \x00\x00\x00\x00]
2026-10-30 07:15:49.673 S2896 >> [P]
2026-10-30 07:15:49.782 S2896 .. EERP matched to DESADV_HARROWFLD_061602.edi (sent 30 Oct 06:17): delivered
2026-10-30 07:15:49.942 S2896 << [HHARROWFLD.DELFOR             202610300715490001        O0013FENWRAY3004         O0013HARROWFLD6335       U000000000000000037000000000003700000000000000000000000N000]
2026-10-30 07:15:50.107 S2896 >> [200000000000000000]
2026-10-30 07:15:50.336 S2896 .. DATA: 10 exchange buffer(s), 37794 octets
2026-10-30 07:15:50.394 S2896 << [T0000000000000000000000000000037794]
2026-10-30 07:15:50.518 S2896 >> [4N]
2026-10-30 07:15:50.631 S2896 .. stored as inbound/DELFOR_HARROWFLD_071549.edi
2026-10-30 07:15:50.642 S2896 << [R]
2026-10-30 07:15:50.727 S2896 >> [EHARROWFLD.DELFOR             202610300715490001        O0013HARROWFLD6335       O0013FENWRAY3004         \x00\x00\x00\x00]
2026-10-30 07:15:50.787 S2896 << [P]
2026-10-30 07:15:50.937 S2896 >> [R]
2026-10-30 07:15:51.016 S2896 << [F00000\x0D]
2026-10-30 07:15:51.025 S2896 .. session closed
2026-10-30 07:16:35.000 ----- .. outbound TCP connect to oftp.pemberline.example (203.0.113.108) timed out after 30 s, retry in 120 s
2026-10-30 07:19:31.000 S2903 .. session S2903: TCP connect to oftp.pemberline.example (203.0.113.108), TLS 1.3 established
2026-10-30 07:19:31.166 S2903 << [IODETTE FTP READY \x0D]
2026-10-30 07:19:31.185 S2903 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 07:19:31.211 S2903 << [X5O0013PEMBERLINE8594      ********04096BNYN064N            \x0D]
2026-10-30 07:19:31.295 S2903 .. queued DESADV_PEMBERLINE_071554.edi
2026-10-30 07:19:31.398 S2903 >> [HFENWRAY.DESADV               202610300715540001        O0013PEMBERLINE8594      O0013FENWRAY3004         U000000000000000010000000000001000000000000000000000000N000]
2026-10-30 07:19:31.500 S2903 << [200000000000000000]
2026-10-30 07:19:31.882 S2903 .. DATA: 3 exchange buffer(s), 9915 octets
2026-10-30 07:19:32.018 S2903 >> [T0000000000000000000000000000009915]
2026-10-30 07:19:32.192 S2903 << [4N]
2026-10-30 07:19:32.226 S2903 .. file transferred, awaiting EERP
2026-10-30 07:19:32.368 S2903 >> [R]
2026-10-30 07:19:32.512 S2903 << [F00000\x0D]
2026-10-30 07:19:32.554 S2903 .. session closed
2026-10-30 07:22:20.000 S2899 .. session S2899: TCP connect to oftp.thornvale.example (203.0.113.133), TLS 1.3 established
2026-10-30 07:22:20.161 S2899 << [IODETTE FTP READY \x0D]
2026-10-30 07:22:20.285 S2899 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 07:22:20.347 S2899 << [X5O0013THORNVALE2316       ********04096BNYN064N            \x0D]
2026-10-30 07:22:20.410 S2899 .. queued INVOIC_THORNVALE_072146.edi
2026-10-30 07:22:20.514 S2899 >> [HFENWRAY.INVOIC               202610300721460001        O0013THORNVALE2316       O0013FENWRAY3004         U000000000000000048000000000004800000000000000000000000N000]
2026-10-30 07:22:20.611 S2899 << [200000000000000000]
2026-10-30 07:22:20.794 S2899 .. DATA: 12 exchange buffer(s), 48701 octets
2026-10-30 07:22:20.861 S2899 >> [T0000000000000000000000000000048701]
2026-10-30 07:22:21.022 S2899 << [4N]
2026-10-30 07:22:21.094 S2899 .. file transferred, awaiting EERP
2026-10-30 07:22:21.145 S2899 >> [R]
2026-10-30 07:22:21.277 S2899 << [F00000\x0D]
2026-10-30 07:22:21.399 S2899 .. session closed
2026-10-30 07:29:27.554 S2904 .. session S2904: inbound TCP connection from 203.0.113.108, TLS 1.3 established
2026-10-30 07:29:27.672 S2904 >> [IODETTE FTP READY \x0D]
2026-10-30 07:29:27.788 S2904 << [X5O0013PEMBERLINE8594      ********04096BNYN064N            \x0D]
2026-10-30 07:29:27.922 S2904 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 07:29:28.013 S2904 << [EFENWRAY.DESADV               202610300715540001        O0013FENWRAY3004         O0013PEMBERLINE8594      \x00\x00\x00\x00]
2026-10-30 07:29:28.031 S2904 >> [P]
2026-10-30 07:29:28.078 S2904 .. EERP matched to DESADV_PEMBERLINE_071554.edi (sent 30 Oct 07:19): delivered
2026-10-30 07:29:28.108 S2904 << [R]
2026-10-30 07:29:28.130 S2904 >> [F00000\x0D]
2026-10-30 07:29:28.208 S2904 .. session closed
2026-10-30 07:29:36.000 S2901 .. session S2901: TCP connect to oftp.pemberline.example (203.0.113.108), TLS 1.3 established
2026-10-30 07:29:36.064 S2901 << [IODETTE FTP READY \x0D]
2026-10-30 07:29:36.094 S2901 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 07:29:36.194 S2901 << [X5O0013PEMBERLINE8594      ********04096BNYN064N            \x0D]
2026-10-30 07:29:36.313 S2901 .. queued DESADV_PEMBERLINE_072818.edi
2026-10-30 07:29:36.427 S2901 >> [HFENWRAY.DESADV               202610300728180001        O0013PEMBERLINE8594      O0013FENWRAY3004         U000000000000000047000000000004700000000000000000000000N000]
2026-10-30 07:29:36.574 S2901 << [200000000000000000]
2026-10-30 07:29:36.851 S2901 .. DATA: 12 exchange buffer(s), 47539 octets
2026-10-30 07:29:36.882 S2901 >> [T0000000000000000000000000000047539]
2026-10-30 07:29:36.949 S2901 << [4N]
2026-10-30 07:29:37.035 S2901 .. file transferred, awaiting EERP
2026-10-30 07:29:37.116 S2901 >> [R]
2026-10-30 07:29:37.220 S2901 << [F00000\x0D]
2026-10-30 07:29:37.312 S2901 .. session closed
2026-10-30 07:46:42.561 S2898 .. session S2898: inbound TCP connection from 203.0.113.133, TLS 1.3 established
2026-10-30 07:46:42.676 S2898 >> [IODETTE FTP READY \x0D]
2026-10-30 07:46:42.703 S2898 << [X5O0013THORNVALE2316       ********04096BNYN064N            \x0D]
2026-10-30 07:46:42.766 S2898 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 07:46:42.825 S2898 << [EFENWRAY.DESADV               202610300659300001        O0013FENWRAY3004         O0013THORNVALE2316       \x00\x00\x00\x00]
2026-10-30 07:46:42.849 S2898 >> [P]
2026-10-30 07:46:42.994 S2898 .. EERP matched to DESADV_THORNVALE_065930.edi (sent 30 Oct 07:00): delivered
2026-10-30 07:46:43.147 S2898 << [R]
2026-10-30 07:46:43.209 S2898 >> [F00000\x0D]
2026-10-30 07:46:43.238 S2898 .. session closed
2026-10-30 07:49:09.399 S2900 .. session S2900: inbound TCP connection from 203.0.113.133, TLS 1.3 established
2026-10-30 07:49:09.490 S2900 >> [IODETTE FTP READY \x0D]
2026-10-30 07:49:09.580 S2900 << [X5O0013THORNVALE2316       ********04096BNYN064N            \x0D]
2026-10-30 07:49:09.715 S2900 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 07:49:09.865 S2900 << [EFENWRAY.INVOIC               202610300721460001        O0013FENWRAY3004         O0013THORNVALE2316       \x00\x00\x00\x00]
2026-10-30 07:49:09.954 S2900 >> [P]
2026-10-30 07:49:10.005 S2900 .. EERP matched to INVOIC_THORNVALE_072146.edi (sent 30 Oct 07:22): delivered
2026-10-30 07:49:10.144 S2900 << [R]
2026-10-30 07:49:10.254 S2900 >> [F00000\x0D]
2026-10-30 07:49:10.319 S2900 .. session closed
2026-10-30 08:00:20.312 S2902 .. session S2902: inbound TCP connection from 203.0.113.108, TLS 1.3 established
2026-10-30 08:00:20.469 S2902 >> [IODETTE FTP READY \x0D]
2026-10-30 08:00:20.648 S2902 << [X5O0013PEMBERLINE8594      ********04096BNYN064N            \x0D]
2026-10-30 08:00:20.782 S2902 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 08:00:20.948 S2902 << [EFENWRAY.DESADV               202610300728180001        O0013FENWRAY3004         O0013PEMBERLINE8594      \x00\x00\x00\x00]
2026-10-30 08:00:21.065 S2902 >> [P]
2026-10-30 08:00:21.163 S2902 .. EERP matched to DESADV_PEMBERLINE_072818.edi (sent 30 Oct 07:29): delivered
2026-10-30 08:00:21.225 S2902 << [HPEMBERLINE.DELJIT            202610300800210001        O0013FENWRAY3004         O0013PEMBERLINE8594      U000000000000000039000000000003900000000000000000000000N000]
2026-10-30 08:00:21.358 S2902 >> [200000000000000000]
2026-10-30 08:00:21.537 S2902 .. DATA: 10 exchange buffer(s), 38971 octets
2026-10-30 08:00:21.711 S2902 << [T0000000000000000000000000000038971]
2026-10-30 08:00:21.814 S2902 >> [4N]
2026-10-30 08:00:21.923 S2902 .. stored as inbound/DELJIT_PEMBERLINE_080021.edi
2026-10-30 08:00:22.062 S2902 << [R]
2026-10-30 08:00:22.231 S2902 >> [EPEMBERLINE.DELJIT            202610300800210001        O0013PEMBERLINE8594      O0013FENWRAY3004         \x00\x00\x00\x00]
2026-10-30 08:00:22.407 S2902 << [P]
2026-10-30 08:00:22.584 S2902 >> [R]
2026-10-30 08:00:22.616 S2902 << [F00000\x0D]
2026-10-30 08:00:22.792 S2902 .. session closed
2026-10-30 08:07:36.000 S2909 .. session S2909: TCP connect to oftp.calderbank.example (203.0.113.141), TLS 1.3 established
2026-10-30 08:07:36.031 S2909 << [IODETTE FTP READY \x0D]
2026-10-30 08:07:36.105 S2909 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 08:07:36.180 S2909 << [X5O0013CALDERBANK4600      ********04096BNYN064N            \x0D]
2026-10-30 08:07:36.228 S2909 .. queued INVOIC_CALDERBANK_080645.edi
2026-10-30 08:07:36.278 S2909 >> [HFENWRAY.INVOIC               202610300806450001        O0013CALDERBANK4600      O0013FENWRAY3004         U000000000000000031000000000003100000000000000000000000N000]
2026-10-30 08:07:36.337 S2909 << [200000000000000000]
2026-10-30 08:07:36.493 S2909 .. DATA: 8 exchange buffer(s), 31642 octets
2026-10-30 08:07:36.640 S2909 >> [T0000000000000000000000000000031642]
2026-10-30 08:07:36.719 S2909 << [4N]
2026-10-30 08:07:36.851 S2909 .. file transferred, awaiting EERP
2026-10-30 08:07:36.876 S2909 >> [R]
2026-10-30 08:07:36.970 S2909 << [F00000\x0D]
2026-10-30 08:07:36.995 S2909 .. session closed
2026-10-30 08:45:55.000 ----- .. outbound TCP connect to oftp.harrowfld.example (203.0.113.153) timed out after 30 s, retry in 120 s
2026-10-30 08:48:38.000 S2893 .. session S2893: TCP connect to oftp.harrowfld.example (203.0.113.153), TLS 1.3 established
2026-10-30 08:48:38.084 S2893 << [IODETTE FTP READY \x0D]
2026-10-30 08:48:38.203 S2893 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 08:48:38.345 S2893 << [X5O0013HARROWFLD6335       ********04096BNYN064N            \x0D]
2026-10-30 08:48:38.520 S2893 .. queued DESADV_HARROWFLD_084528.edi
2026-10-30 08:48:38.657 S2893 >> [HFENWRAY.DESADV               202610300845280001        O0013HARROWFLD6335       O0013FENWRAY3004         U000000000000000031000000000003100000000000000000000000N000]
2026-10-30 08:48:38.829 S2893 << [200000000000000000]
2026-10-30 08:48:39.130 S2893 .. DATA: 8 exchange buffer(s), 31214 octets
2026-10-30 08:48:39.229 S2893 >> [T0000000000000000000000000000031214]
2026-10-30 08:48:39.280 S2893 << [4N]
2026-10-30 08:48:39.460 S2893 .. file transferred, awaiting EERP
2026-10-30 08:48:39.552 S2893 >> [R]
2026-10-30 08:48:39.697 S2893 << [F00000\x0D]
2026-10-30 08:48:39.846 S2893 .. session closed
2026-10-30 08:53:29.995 S2910 .. session S2910: inbound TCP connection from 203.0.113.141, TLS 1.3 established
2026-10-30 08:53:30.077 S2910 >> [IODETTE FTP READY \x0D]
2026-10-30 08:53:30.186 S2910 << [X5O0013CALDERBANK4600      ********04096BNYN064N            \x0D]
2026-10-30 08:53:30.225 S2910 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 08:53:30.262 S2910 << [EFENWRAY.INVOIC               202610300806450001        O0013FENWRAY3004         O0013CALDERBANK4600      \x00\x00\x00\x00]
2026-10-30 08:53:30.294 S2910 >> [P]
2026-10-30 08:53:30.329 S2910 .. EERP matched to INVOIC_CALDERBANK_080645.edi (sent 30 Oct 08:07): delivered
2026-10-30 08:53:30.398 S2910 << [R]
2026-10-30 08:53:30.553 S2910 >> [F00000\x0D]
2026-10-30 08:53:30.698 S2910 .. session closed
2026-10-30 09:04:18.846 S2894 .. session S2894: inbound TCP connection from 203.0.113.153, TLS 1.3 established
2026-10-30 09:04:18.949 S2894 >> [IODETTE FTP READY \x0D]
2026-10-30 09:04:18.960 S2894 << [X5O0013HARROWFLD6335       ********04096BNYN064N            \x0D]
2026-10-30 09:04:19.086 S2894 >> [X5O0013FENWRAY3004         ********04096BNYN064N            \x0D]
2026-10-30 09:04:19.157 S2894 << [EFENWRAY.DESADV               202610300845280001        O0013FENWRAY3004         O0013HARROWFLD6335       \x00\x00\x00\x00]
2026-10-30 09:04:19.214 S2894 >> [P]
2026-10-30 09:04:19.339 S2894 .. EERP matched to DESADV_HARROWFLD_084528.edi (sent 30 Oct 08:48): delivered
2026-10-30 09:04:19.474 S2894 << [HHARROWFLD.DELJIT             202610300904190001        O0013FENWRAY3004         O0013HARROWFLD6335       U000000000000000022000000000002200000000000000000000000N000]
2026-10-30 09:04:19.575 S2894 >> [200000000000000000]
2026-10-30 09:04:19.651 S2894 .. DATA: 6 exchange buffer(s), 21623 octets
2026-10-30 09:04:19.711 S2894 << [T0000000000000000000000000000021623]
2026-10-30 09:04:19.758 S2894 >> [4N]
2026-10-30 09:04:19.902 S2894 .. stored as inbound/DELJIT_HARROWFLD_090419.edi
2026-10-30 09:04:19.929 S2894 << [R]
2026-10-30 09:04:19.965 S2894 >> [EHARROWFLD.DELJIT             202610300904190001        O0013HARROWFLD6335       O0013FENWRAY3004         \x00\x00\x00\x00]
2026-10-30 09:04:20.003 S2894 << [P]
2026-10-30 09:04:20.071 S2894 >> [R]
2026-10-30 09:04:20.222 S2894 << [F00000\x0D]
2026-10-30 09:04:20.342 S2894 .. session closed
```

## Document 3: Gateway file status report (sender side) (gateway_status.txt)

```text
Fenwray Castings Ltd: OFTP2 gateway file status
Generated 2026-10-30 09:00. Outbound files, all partners.

Sent             Partner                        File                                         Octets  Status
2026-10-30 02:10 Marrowgate Motor Works         INVOICES_20261030_NIGHT.edi                50331648  REFUSED at end of file after restart (EFNA)
2026-10-30 02:12 Ostley Fasteners               DESADV_OSTLEY_20261030_NIGHT.edi           27435227  delivered after restart, EERP 30 Oct 03:02
2026-10-30 05:04 Pemberline Plastics            DESADV_PEMBERLINE_050335.edi                  42774  delivered, EERP 30 Oct 05:49
2026-10-30 05:58 Calderbank Wiring              DESADV_CALDERBANK_055802.edi                  54709  delivered, EERP 30 Oct 06:24
2026-10-30 06:08 Marrowgate Motor Works         INVOICES_20261030_NIGHT.edi (manual rese   50331648  delivered, EERP
2026-10-30 06:17 Harrowfield Glass              DESADV_HARROWFLD_061602.edi                   38688  delivered, EERP 30 Oct 07:15
2026-10-30 07:00 Thornvale Logistics            DESADV_THORNVALE_065930.edi                   46077  delivered, EERP 30 Oct 07:46
2026-10-30 07:19 Pemberline Plastics            DESADV_PEMBERLINE_071554.edi                   9915  delivered, EERP 30 Oct 07:29
2026-10-30 07:22 Thornvale Logistics            INVOIC_THORNVALE_072146.edi                   48701  delivered, EERP 30 Oct 07:49
2026-10-30 07:29 Pemberline Plastics            DESADV_PEMBERLINE_072818.edi                  47539  delivered, EERP 30 Oct 08:00
2026-10-30 08:07 Calderbank Wiring              INVOIC_CALDERBANK_080645.edi                  31642  delivered, EERP 30 Oct 08:53
2026-10-30 08:48 Harrowfield Glass              DESADV_HARROWFLD_084528.edi                   31214  delivered, EERP 30 Oct 09:04
```

## Document 4: EDIFACT interchange the ticket is about (excerpt of the start and end, as transmitted) (interchange.edi)

```text
UNB+UNOA:3+FENWRAY89:ZZZ+MARROWGATE28:ZZZ+261030:0210+898879'UNH+1+INVOIC:D:96A:UN'BGM+380+INV74101+9'DTM+137:20261030:102'NAD+SE+++FENWRAY CASTINGS LTD'NAD+BY+++MARROWGATE MOTOR WORKS'CUX+2:EUR:4'LIN+1++P-75154:IN'QTY+47:141'MOA+203:6081.33'PRI+AAA:43.13'LIN+2++P-31014:IN'QTY+47:331'MOA+203:5239.73'PRI+AAA:15.83'LIN+3++P-17237:IN'QTY+47:238'MOA+203:11207.42'PRI+AAA:47.09'UNS+S'MOA+77:27034.17'TAX+7+VAT+++:::20+S'MOA+124:4505.69'UNT+23+1'UNH+2+INVOIC:D:96A:UN'BGM+380+INV65510+9'DTM+137:20261030:102'NAD+SE+++FENWRAY CASTINGS LTD'NAD+BY+++MARROWGATE MOTOR WORKS'CUX+2:EUR:4'LIN+1++P-56488:IN'QTY+47:294'MOA+203:2401.98'PRI+AAA:8.17'UNS+S'MOA+77:2882.37'TAX+7+VAT+++:::20+S'MOA+124:480.39'UNT+15+2'
[... 32085 further INVOIC messages not shown ...]
UNH+32088+INVOIC:D:96A:UN'BGM+380+INV30869+9'DTM+137:20261030:102'NAD+SE+++FENWRAY CASTINGS LTD'NAD+BY+++MARROWGATE MOTOR WORKS'CUX+2:EUR:4'LIN+1++P-40909:IN'QTY+47:342'MOA+203:7691.58'PRI+AAA:22.49'LIN+2++P-65127:IN'QTY+47:33'MOA+203:1497.87'PRI+AAA:45.39'UNS+S'MOA+77:11027.34'TAX+7+VAT+++:::20+S'MOA+124:1837.89'UNT+19+32088'UNZ+32088+898879'
```

## Document 5: Partner response (partner_response.txt)

```text
From: Kim Price, EDI operations, Marrowgate Motor Works
To: Jordan Tanaka, Fenwray Castings Ltd
Subject: RE: restarted transfers

Hello,

We see the byte count errors on your restarted transfers. Restarted transfers from our other suppliers complete normally, and your 06:00 resend arrived fine. Please check your gateway.

Regards,
Kim Price
```

## Document 6: Specification extracts (spec_extracts.txt)

```text
RFC 5024 (ODETTE File Transfer Protocol 2), section 1.5.4. Verbatim extract.

1.5.4.  Restart

   ODETTE-FTP can negotiate the restart of an interrupted Virtual File
   transmission.  Fixed and Variable format files are restarted on
   record boundaries.  For Unstructured and Text files, the restart
   position is expressed as a file offset in 1K (1024 octet) blocks.

   The restart position is always calculated relative to the start of
   the Virtual File.

RFC 5024 (ODETTE File Transfer Protocol 2), section 4.3.3. Verbatim extract.

4.3.3.  Restart Facilities

   The Start File command includes a count allowing the restart of an
   interrupted transmission to be negotiated.  If restart facilities are
   not available, the restart count must be set to zero.  The sender
   will start with the lowest record count + 1.

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

RFC 5024 (ODETTE File Transfer Protocol 2), section 5.3.4. Verbatim extract.

5.3.4.  SFPA - Start File Positive Answer

   o-------------------------------------------------------------------o
   |       SFPA        Start File Positive Answer                      |
   |                                                                   |
   |       Start File Phase           Speaker <---- Listener           |
   |-------------------------------------------------------------------|
   | Pos | Field     | Description                           | Format  |
   |-----+-----------+---------------------------------------+---------|
   |   0 | SFPACMD   | SFPA Command, '2'                     | F X(1)  |
   |   1 | SFPAACNT  | Answer Count                          | V 9(17) |
   o-------------------------------------------------------------------o

   SFPACMD   Command Code                                      Character

      Value: '2'  SFPA Command identifier.

   SFPAACNT  Answer Count                                    Numeric(17)

             The Listener must enter a count lower than or equal to the
             restart count specified by the Speaker in the Start File
             (SFID) command.  The count expresses the received user
             data.  If restart facilities are not available, a count of
             zero must be specified.

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

value: a JSON string holding how many octets of the file the receiver held from the interrupted transfer when the restart began, as a plain integer.

Example of the format only (not a hint):
```json
{"cause": "file_too_large", "layer": "transport", "owner": "receiver", "location": ["SFID.SFIDFSIZ"], "next_check": "none", "value": "12345"}
```
