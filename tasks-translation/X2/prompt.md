# Translation task X2

Translate the sender's in-house invoice file below into the EDIFACT interchange that the mapping specification defines. Reply with your working if you like, but end your reply with the complete interchange in one fenced ```edifact block. Only the last ```edifact block is graded, segment by segment, against the exact expected interchange; line breaks between segments are ignored.

## In-house invoice file (fixed width)

```text
HIV643240  20261026EURMüller & Söhne Fahrzeugtechnik GmbH
L001BRKT 45:A      000013500PCE000001250000
L002SEAL?RING-7    000008000PCE000000001250
L003KL+20/4        000001250KGM000000045000
L004BRKT 45:A      000005000PCE000000033335
L005HUB-9031       000003500MTR000000010050
T0005
```

## Mapping specification

```text
MAPPING SPECIFICATION: in-house invoice flat file to EDIFACT INVOIC D.96A
(written for this evaluation; it is the only authority for this task)

Input: fixed-width records, positions counted in characters from 1.
  H record: pos 1 'H'; 2-11 invoice number (left-justified, space padded);
            12-19 invoice date CCYYMMDD; 20-22 currency; 23-57 buyer name (UTF-8).
  L record: pos 1 'L'; 2-4 line number; 5-19 part number (left-justified, space
            padded); 20-28 quantity, 9 digits, 3 implied decimals; 29-31 unit of
            measure; 32-43 unit price, 12 digits, 4 implied decimals.
  T record: pos 1 'T'; 2-5 number of L records.

Output: one interchange, syntax UNOA version 3, default service characters
(UNA not sent), release character ? before any of ? + : ' inside a value.
Segments, in this order:
  UNB+UNOA:3+QUILLMERE07:ZZ+MARROWGATE13:ZZ+261102:0926+009910'
  UNH+1+INVOIC:D:96A:UN'
  BGM+380+<invoice number, trailing spaces removed>+9'
  DTM+137:<invoice date>:102'
  NAD+BY+++<buyer name, see below>'
  CUX+2:<currency>:4'
  per L record, in file order:
    LIN+<line number without leading zeros>++<part number, trailing spaces removed>:IN'
    QTY+47:<quantity>:<unit of measure>'
    MOA+203:<line amount>'
    PRI+AAA:<unit price>'
  UNS+S'
  MOA+77:<invoice total>'
  TAX+7+VAT+++:::20+S'
  MOA+124:<VAT amount>'
  UNT+<number of segments from UNH to UNT, both included>+1'
  UNZ+1+009910'

Values:
  quantity, unit price: decimal mark '.', no leading zeros, no trailing zeros
    after the decimal mark, no decimal mark for whole numbers (12.500 -> 12.5,
    7.000 -> 7, 0.250 -> 0.25).
  line amount = quantity x unit price, rounded half up to 2 decimals, always
    written with exactly 2 decimals (156.25, 40.00).
  VAT amount = 20 % of the sum of the line amounts, rounded half up to 2
    decimals, exactly 2 decimals. invoice total = sum of line amounts + VAT
    amount, exactly 2 decimals.
  buyer name: (1) replace A-umlaut by AE, O-umlaut by OE, U-umlaut by UE (either
    case), sharp s by SS, e-acute and e-grave by E, a-ring by A, o-slash by O;
    (2) convert to upper case; (3) replace every character not in
    A-Z 0-9 space . , - ( ) / = ' + : ? by a space; (4) replace runs of spaces by
    one space and remove leading and trailing spaces; (5) cut to the first 35
    characters, then remove trailing spaces; (6) add release characters.
    Release characters do not count towards the 35.
```
