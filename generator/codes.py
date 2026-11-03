"""Every protocol code and convention the tickets depend on.

Two kinds of entry:

* Reason and action codes (kind="code"). Until Houman sets verified=True,
  the generator writes a visible placeholder <<UNVERIFIED:KEY>> into the
  ticket instead of the value.
* Conventions (kind="convention"): segment layouts, element numbering,
  message versions, qualifiers. These are rendered (a ticket cannot be
  written without them) but are tracked the same way.

A release build (python -m generator.build --release) refuses to run while
any entry a ticket uses is unverified.

quoted=True means the candidate value was copied from the specification
text during the build session (see source). It still needs Houman's check.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    key: str
    kind: str          # "code" or "convention"
    value: str         # candidate value
    meaning: str
    source: str
    quoted: bool = False
    verified: bool = False
    tag: str = ""      # opaque letters-only id, so a placeholder never hints at the meaning or a value


_ENTRIES = [
    # ---- OFTP2 reason codes, quoted from RFC 5024 on 30 Oct 2026 ----
    Entry("OFTP2.SFNAREAS.DUPLICATE_FILE", "code", "13", "Duplicate file.",
          "RFC 5024 s5.3.5 SFNAREAS", quoted=True, tag="PA"),
    Entry("OFTP2.ESIDREAS.NORMAL", "code", "00", "Normal session termination",
          "RFC 5024 s5.3.11 ESIDREAS", quoted=True, tag="PB"),
    Entry("OFTP2.NERPREAS.FILE_PROCESSING_FAILED", "code", "34", "File processing failed.",
          "RFC 5024 s5.3.14 NERPREAS", quoted=True, tag="PC"),
    Entry("OFTP2.EFNAREAS.UNSPECIFIED", "code", "99", "Unspecified reason.",
          "RFC 5024 s5.3.10 EFNAREAS", quoted=True, tag="PE"),
    Entry("OFTP2.EFNAREAS.INVALID_BYTE_COUNT", "code", "11", "Invalid byte count.",
          "RFC 5024 s5.3.10 EFNAREAS", quoted=True, tag="PJ"),
    Entry("OFTP2.NERPREAS.SFNA13_DUPLICATE_FILE", "code", "23",
          "SFNA(RETRY=N) received with reason code '13' (duplicate file)",
          "RFC 5024 s5.3.14 NERPREAS", quoted=True, tag="PD"),

    # ---- EDIFACT CONTRL codes, quoted from CONTRL D.3 (spec/unedifact) ----
    Entry("EDIFACT.0083.REJECTED", "code", "4",
          "This level and all lower levels rejected",
          "CONTRL D.3 (ISO/TC 154/JWG 1 v3-Contrl.pdf), code list 0083", quoted=True, tag="PF"),
    Entry("EDIFACT.0085.REFERENCES_DO_NOT_MATCH", "code", "28",
          "References do not match (control reference in UNB/UNH differs from UNZ/UNT)",
          "CONTRL D.3 (ISO/TC 154/JWG 1 v3-Contrl.pdf), code list 0085", quoted=True, tag="PG"),
    Entry("EDIFACT.0085.SYNTAX_LEVEL_NOT_SUPPORTED", "code", "2",
          "Syntax version or level not supported",
          "CONTRL D.3 (ISO/TC 154/JWG 1 v3-Contrl.pdf), code list 0085", quoted=True, tag="PI"),
    Entry("EDIFACT.0085.UNSPECIFIED_ERROR", "code", "18", "Unspecified error",
          "CONTRL D.3 (ISO/TC 154/JWG 1 v3-Contrl.pdf), code list 0085", quoted=True, tag="PK"),
    Entry("EDIFACT.0085.UNKNOWN_INTERCHANGE_SENDER", "code", "23",
          "Unknown Interchange sender",
          "CONTRL D.3 (ISO/TC 154/JWG 1 v3-Contrl.pdf), code list 0085", quoted=True, tag="PH"),

    # ---- EDIFACT conventions, from the sources in spec/SOURCES.md unless marked ----
    Entry("EDIFACT.LAYOUT.UNB", "convention",
          "UNB+S001(0001:0002)+S002(0004:0007:0008)+S003(0010:0007:0014)+S004(0017:0019)+0020",
          "Interchange header layout, syntax version 3",
          "UNECE syntax rules Annex B (d422_s.htm), segment UNB", quoted=True),
    Entry("EDIFACT.LAYOUT.UNZ", "convention", "UNZ+0036+0020",
          "Interchange trailer layout", "UNECE syntax rules Annex B (d422_s.htm), segment UNZ",
          quoted=True),
    Entry("EDIFACT.LAYOUT.UCI", "convention",
          "UCI+0020+S002+S003+0083+0085+0013+S011(0098:0104)",
          "CONTRL interchange response segment layout",
          "CONTRL D.3 (ISO/TC 154/JWG 1 v3-Contrl.pdf), segment UCI", quoted=True),
    Entry("EDIFACT.S011.POSITION_COUNTING", "convention",
          "0098 counts data elements after the tag from 1; 0104 counts components from 1",
          "How the erroneous position in UCI S011 is counted",
          "general knowledge: CONTRL D.3 defines S011 but not the counting rule"),
    Entry("EDIFACT.CONTRL.MESSAGE_ID_SYNTAX3", "convention", "CONTRL:D:3:UN",
          "UNH S009 for a CONTRL answering a syntax version 3 interchange",
          "CONTRL D.3 (ISO/TC 154/JWG 1 v3-Contrl.pdf): version D, release 3, agency UN",
          quoted=True),
    Entry("EDIFACT.LAYOUT.UNB_TAIL", "convention",
          "after 0020: S005 (6), 0026 (7), 0029 (8), 0031 (9), 0032 (10), 0035 (11)",
          "Order and positions of the optional UNB elements after 0020; 0035 = 1 means test",
          "UNECE syntax rules Annex B (d422_s.htm), segment UNB; JWG 1 code list 0035",
          quoted=True),
    Entry("EDIFACT.LAYOUT.UNG_UNE", "convention",
          "UNG+0038+S006+S007+S004+0048+0051+S008; UNE+0060+0048",
          "Functional group header and trailer layout, syntax version 3",
          "UNECE syntax rules Annex B (d422_s.htm), segments UNG and UNE", quoted=True),
    Entry("EDIFACT.UNZ.0036_COUNTS_GROUPS", "convention",
          "UNZ 0036 counts functional groups when UNG is used, otherwise messages",
          "Interchange control count when functional groups are present (E1 depends on this)",
          "UNECE syntax implementation guidelines (d423.htm), UNZ first element", quoted=True),
    # ---- SAP facts (Amendment 1), general knowledge, NOT quoted, closed book ----
    Entry("SAP.IDOC.STATUS_53", "convention", "53",
          "Inbound IDoc: application document posted", "SAP standard IDoc status values"),
    Entry("SAP.IDOC.STATUS_64", "convention", "64",
          "Inbound IDoc: ready to be transferred to the application (waiting to be processed)",
          "SAP standard IDoc status values"),
    Entry("SAP.IDOC.STATUS_56", "convention", "56",
          "Inbound IDoc added with errors, typically no inbound partner profile for the "
          "sender partner and message type", "SAP standard IDoc status values"),
    Entry("SAP.PROGRAM.RBDAPP01", "convention", "RBDAPP01",
          "Report that passes inbound IDocs in status 64 to the application when the partner "
          "profile is set to processing by background program", "SAP standard ALE/EDI reports"),
    Entry("SAP.PARTNER_TYPE.LI", "convention", "LI", "Partner type vendor (supplier)",
          "SAP partner types in IDoc control record SNDPRT/RCVPRT"),
    Entry("EDIFACT.UNB.S004_FORMAT_SYNTAX3", "convention", "YYMMDD:HHMM",
          "Date and time of preparation format in syntax version 3: 0017 is n6 (YYMMDD), "
          "0019 is n4 (HHMM); CCYYMMDD in 0017 is a syntax version 4 format",
          "UNECE syntax rules Annex B (d422_s.htm), composite S004", quoted=True),
    Entry("EDIFACT.0007.MUTUALLY_DEFINED", "convention", "ZZ",
          "Identification code qualifier for mutually defined IDs",
          "NOT FOUND: JWG 1 code list 0007 has ZZZ Mutually defined and no ZZ"),
    Entry("EDIFACT.INVOIC.D96A.BODY", "convention", "illustrative",
          "INVOIC D.96A message body (not graded; the planted fault is never in the body)",
          "UNECE directory D.96A, message INVOIC"),
]

ENTRIES = {e.key: e for e in _ENTRIES}


assert len({e.tag for e in _ENTRIES if e.kind == "code"}) == sum(e.kind == "code" for e in _ENTRIES)


def placeholder(key: str) -> str:
    return f"<<UNVERIFIED-{ENTRIES[key].tag}>>"
