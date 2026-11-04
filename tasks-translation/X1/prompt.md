# Translation task X1

Translate the despatch advice below into the Customer's in-house JSON that the mapping specification defines. Reply with your working if you like, but end your reply with the complete JSON object in one fenced ```json block. Only the last ```json block is graded, against the exact expected object.

## EDIFACT DESADV as received (no line breaks)

```text
UNB+UNOA:3+QUILLMERE07:ZZZ+MARROWGATE11:ZZZ+261102:0715+004721'UNH+1+DESADV:D:96A:UN'BGM+351+DN492757+9'DTM+137:20261102:102'DTM+11:20261026:102'NAD+SU+++QUILLMERE DRIVETRAIN LTD'NAD+ST+++MARROWGATE MOTOR WORKS'CPS+1'CPS+2+1'PAC+1++PX'PCI+17'GIN+ML+LBL38414879'CPS+3+2'PAC+1++CTN'PCI+17'GIN+ML+LBL02844027'LIN+1++AX-4471/B:IN'QTY+12:66:KGM'CPS+5+1'PAC+1++PX'PCI+17'GIN+ML+LBL75286258'LIN+2++HUB-9031:IN'QTY+12:40:PCE'CPS+6+5'PAC+1++CTN'PCI+17'GIN+ML+LBL36192323'LIN+3++BRKT 45?:A:IN'QTY+12:26:KGM'LIN+4++SEAL??RING-7:IN'QTY+12:250:PCE'CPS+4+2'PAC+1++CTN'PCI+17'GIN+ML+LBL93468265'LIN+5++BRKT 45?:A:IN'QTY+12:65:PCE'CPS+9+1'PAC+1++PX'PCI+17'GIN+ML+LBL60362102'LIN+6++BRKT 45?:A:IN'QTY+12:12:PCE'CPS+8+5'PAC+1++CTN'PCI+17'GIN+ML+LBL70483176'LIN+7++BRKT 45?:A:IN'QTY+12:19:KGM'CPS+10+9'PAC+1++CTN'PCI+17'GIN+ML+LBL51214392'LIN+8++BRKT 45?:A:IN'QTY+12:33:PCE'LIN+9++KL?+20/4:IN'QTY+12:50:KGM'UNT+58+1'UNZ+1+004721'
```

## Mapping specification

```text
MAPPING SPECIFICATION: EDIFACT DESADV D.96A to the Customer's in-house JSON
(written for this evaluation; it is the only authority for this task)

Input structure used by the Supplier:
  CPS+<id>' with no parent is the shipment. CPS+<id>+<parent id>' is a package
  whose parent is the CPS with that id; the PAC, PCI, GIN and LIN/QTY segments
  that follow a CPS, up to the next CPS, belong to it. PAC 7065 PX = pallet,
  CTN = carton. GIN+ML+<label>' is the package label. LIN+<n>++<part>:IN' with
  QTY+12:<quantity>:<unit>' is an item in that package. Packages may appear in
  any order; the parent id, not the position, decides where a package belongs.
  Values may contain release characters (?) that must be removed.

Output: one JSON object:
  {"despatch_note": <BGM 1004>,
   "despatch_date": <DTM 11 date as YYYY-MM-DD>,
   "pallets": [ one object per pallet, ordered by CPS id ascending:
       {"label": <GIN label>,
        "loose_items": [items directly in the pallet, in input order],
        "cartons": [ one object per carton in this pallet, ordered by CPS id
                     ascending: {"label": <GIN label>, "items": [items, in input order]} ]} ],
   "totals": [ {"part": <part>, "unit": <unit>, "quantity": <sum over all items
                with that part and unit>} sorted by part, then unit, ascending
               (plain character order) ]}
  An item is {"part": <part number>, "unit": <unit>, "quantity": <number>}.
  Quantities are JSON numbers. Keys and nesting exactly as above.
```
