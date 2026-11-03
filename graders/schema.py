"""Answer schema: the single source of truth for the four graded fields.

The prompt text, answer_schema.json and the grader are all built from
this module, so they cannot drift apart.
"""

# Alphabetical on purpose: grouping by layer would give the layer away.
CAUSES = {
    "authentication_failure":
        "The OFTP2 session could not be established because a password, "
        "identification code or secure authentication check failed.",
    "idoc_awaiting_processing":
        "Inbound IDocs were created in the receiver's SAP system but were not passed to the "
        "application, because the scheduled processing that should pick them up did not run.",
    "idoc_mapping_error":
        "The receiver's EDI converter mapped a correct interchange to an incorrect IDoc.",
    "sap_master_data_error":
        "Posting in the receiver's SAP system failed because of its master data "
        "(material, vendor, purchase order).",
    "receiver_partner_setup_missing":
        "The receiver has not set up the sender as agreed (EDI converter partner mapping or "
        "SAP partner profile).",
    "certificate_problem":
        "A TLS or file-security certificate is expired, untrusted or not the one "
        "in the agreement.",
    "character_set_violation":
        "The interchange contains characters outside the agreed syntax "
        "identifier's character repertoire.",
    "compression_not_agreed":
        "A file was sent compressed (or uncompressed) contrary to what the "
        "receiver accepts.",
    "duplicate_interchange":
        "An interchange was rejected because its interchange control reference "
        "was already received from this sender.",
    "duplicate_virtual_file":
        "A virtual file was refused because a virtual file with the same "
        "identification was already delivered.",
    "end_to_end_response_not_returned":
        "The file was delivered but the final recipient never returned the "
        "end-to-end response.",
    "envelope_element_format_invalid":
        "A UNB or UNZ data element has a value whose format or length the "
        "syntax version declared in UNB S001 does not allow.",
    "file_too_large":
        "The file exceeds a size limit of the receiver.",
    "interchange_control_count_mismatch":
        "The interchange control count in UNZ does not match the number of "
        "messages in the interchange.",
    "interchange_control_reference_mismatch":
        "The interchange control reference in UNB and in UNZ are not identical.",
    "intermediary_fault":
        "A clearing centre or other intermediate location lost, altered or "
        "misrouted the file.",
    "invalid_destination":
        "The OFTP2 destination of the virtual file is not known to the receiver.",
    "not_yet_determinable":
        "The documents fit more than one root cause equally well, so the root cause "
        "cannot be named until a further check is made.",
    "no_sender_side_fault":
        "Nothing the sender transmitted or configured is wrong, the fault lies with the "
        "receiver, and no more specific cause in this list applies.",
    "recipient_identification_mismatch":
        "The interchange recipient identification or its qualifier in UNB is not "
        "the one in the partner agreement.",
    "restart_position_invalid":
        "A restarted transfer used a restart position that is wrong, or resumed "
        "from a position other than the one the receiver confirmed.",
    "sender_identification_mismatch":
        "The interchange sender identification or its qualifier in UNB is not "
        "the one in the partner agreement.",
    "session_parameters_not_negotiated":
        "The sender used an OFTP2 session parameter (credit, buffer size or "
        "similar) outside what was negotiated.",
    "syntax_identifier_not_agreed":
        "UNB S001 declares a syntax identifier or syntax version other than the "
        "agreed one.",
    "test_indicator_mismatch":
        "The interchange is flagged as test (or production) contrary to the "
        "agreement.",
}

LAYERS = {
    "transport": "The OFTP2 session or file transfer, including any intermediate "
                 "location.",
    "envelope": "The EDIFACT interchange envelope (UNB to UNZ), wherever the receiver "
                "checks it (gateway or translator).",
    "application": "The business application side, on either party: an EDI converter or SAP "
                   "IDoc processing.",
    "none": "Only with cause no_sender_side_fault: the fault is on the receiver's side, "
            "outside the layers above.",
    "undetermined": "Only with cause not_yet_determinable.",
}

OWNERS = {
    "sender": "The party that sent the file and raised the ticket must fix it.",
    "receiver": "The trading partner the file is addressed to must fix it.",
    "intermediary": "A clearing centre or other intermediate location between the "
                    "parties must fix it.",
    "agreement": "The partner agreement itself is wrong or inconsistent and must "
                 "be amended before either side can fix the fault.",
    "undetermined": "Only with cause not_yet_determinable.",
}

CHECKS = {
    "none": "The documents already determine the root cause.",
    "request_receiver_gateway_log":
        "Ask the receiver for its OFTP2 gateway log covering the file in question.",
    "request_receiver_translator_log":
        "Ask the receiver for its translator's validation log for the interchange.",
    "request_transmitted_copy":
        "Obtain the file exactly as the sender's gateway transmitted it, not the archived copy.",
    "request_other_gateway_node_trace":
        "Obtain the trace from the sender's other gateway node or nodes.",
    "request_agreement_in_force":
        "Obtain the signed version of the partner agreement currently in force.",
    "request_clearing_centre_trace":
        "Ask the clearing centre for its trace of the file.",
    "check_sender_clock": "Check the sender gateway's system clock.",
    "check_certificates": "Check the TLS and file-security certificates on both sides.",
    "resend_unchanged": "Send the same file again unchanged.",
    "resend_with_new_identity": "Send the file again as a new virtual file.",
}

MAX_LOCATIONS = 6

# OFTP2 command -> field names, copied from the command format tables in
# RFC 5024 section 5.3 (command codes and CR fields omitted).
OFTP2_FIELDS = {
    "SSID": ["SSIDLEV", "SSIDCODE", "SSIDPSWD", "SSIDSDEB", "SSIDSR", "SSIDCMPR",
             "SSIDREST", "SSIDSPEC", "SSIDCRED", "SSIDAUTH", "SSIDRSV1", "SSIDUSER"],
    "SFID": ["SFIDDSN", "SFIDRSV1", "SFIDDATE", "SFIDTIME", "SFIDUSER", "SFIDDEST",
             "SFIDORIG", "SFIDFMT", "SFIDLRECL", "SFIDFSIZ", "SFIDOSIZ", "SFIDREST",
             "SFIDSEC", "SFIDCIPH", "SFIDCOMP", "SFIDENV", "SFIDSIGN", "SFIDDESCL",
             "SFIDDESC"],
    "SFPA": ["SFPAACNT"],
    "SFNA": ["SFNAREAS", "SFNARRTR", "SFNAREASL", "SFNAREAST"],
    "EFID": ["EFIDRCNT", "EFIDUCNT"],
    "EFPA": ["EFPACD"],
    "EFNA": ["EFNAREAS", "EFNAREASL", "EFNAREAST"],
    "ESID": ["ESIDREAS", "ESIDREASL", "ESIDREAST"],
    "EERP": ["EERPDSN", "EERPRSV1", "EERPDATE", "EERPTIME", "EERPUSER", "EERPDEST",
             "EERPORIG", "EERPHSHL", "EERPHSH", "EERPSIGL", "EERPSIG"],
    "NERP": ["NERPDSN", "NERPRSV1", "NERPDATE", "NERPTIME", "NERPDEST", "NERPORIG",
             "NERPCREA", "NERPREAS", "NERPREASL", "NERPREAST", "NERPHSHL", "NERPHSH",
             "NERPSIGL", "NERPSIG"],
}

# EDIFACT service segments: element or composite -> components.
# UNVERIFIED convention (see generator/codes.py EDIFACT.LAYOUT.*).
EDIFACT_SEGMENTS = {
    "UNB": {"S001": ["0001", "0002"], "S002": ["0004", "0007", "0008"],
            "S003": ["0010", "0007", "0014"], "S004": ["0017", "0019"],
            "0020": [], "S005": ["0022", "0025"], "0026": [], "0029": [],
            "0031": [], "0032": [], "0035": []},
    "UNZ": {"0036": [], "0020": []},
    "UNG": {"0038": [], "S006": ["0040", "0007"], "S007": ["0044", "0007"],
            "S004": ["0017", "0019"], "0048": [], "0051": [], "S008": ["0052", "0054", "0057"],
            "0058": []},
    "UNE": {"0060": [], "0048": []},
    "UNH": {"0062": [], "S009": ["0065", "0052", "0054", "0051", "0057"]},
    "UNT": {"0074": [], "0062": []},
}


# Application-side objects (Amendment 1: SAP). A location on the application
# layer is written APP.<OBJECT>.
APP_OBJECTS = ["CONVERTER_PARTNER_TABLE", "CONVERTER_MAPPING", "PARTNER_PROFILE",
               "PROCESS_CODE", "BACKGROUND_JOB", "MASTER_DATA", "PORT"]


def all_locations():
    """Every location token the grammar can express (used by the
    list-every-option test)."""
    out = ["NONE", "UNDETERMINED"] + [f"APP.{o}" for o in APP_OBJECTS]
    for cmd, fields in OFTP2_FIELDS.items():
        out += [f"{cmd}.{f}" for f in fields]
    for seg, elems in EDIFACT_SEGMENTS.items():
        for el, comps in elems.items():
            out += [f"{seg}.{el}.{c}" for c in comps] if comps else [f"{seg}.{el}"]
    return out


LOCATION_RULES = ("""\
List the OFTP2 fields, EDIFACT data elements or application objects, on whichever
side, whose values or settings must be changed to fix the root cause, and no
others. If the fault is a conflict between two values that must agree, list both.
Write each one as:
  OFTP2 field:                 COMMAND.FIELD, e.g. "SSID.SSIDCODE"
  EDIFACT simple data element: SEGMENT.ELEMENT, e.g. "UNH.0062"
  EDIFACT component element:   SEGMENT.COMPOSITE.COMPONENT, e.g. "UNB.S003.0010"
  Application-side object:     APP.<OBJECT>, one of """ + ", ".join(APP_OBJECTS) + """
  None of the above must change: "NONE" on its own.
  Root cause not yet determinable: "UNDETERMINED" on its own.""")


def answer_json_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Ticket answer",
        "type": "object",
        "required": ["cause", "layer", "owner", "location", "next_check", "value"],
        "properties": {
            "cause": {"type": "string", "enum": sorted(CAUSES)},
            "layer": {"type": "string", "enum": list(LAYERS)},
            "owner": {"type": "string", "enum": list(OWNERS)},
            "location": {"type": "array", "items": {"type": "string"},
                         "minItems": 1, "maxItems": MAX_LOCATIONS},
            "next_check": {"type": "string", "enum": list(CHECKS)},
            "value": {"type": "string", "description": "ticket-specific exact value"},
        },
    }


def answer_instructions(value_question: str):
    """The 'what to return' section of every prompt."""
    lines = [
        "## What to return",
        "",
        "Diagnose the single root cause of this ticket. Reply in any form you like,",
        "but end your reply with exactly one fenced ```json block holding an object",
        "with these six keys. Only the last ```json block in your reply is graded.",
        "Give one value per key: a key that holds several options, or a list of",
        "alternatives, scores zero for that key.",
        "",
        "cause: exactly one of",
    ]
    for k in sorted(CAUSES):
        lines.append(f"  {k}: {CAUSES[k]}")
    lines += ["", "layer: exactly one of"]
    lines += [f"  {k}: {v}" for k, v in LAYERS.items()]
    lines += ["", "owner: exactly one of (who must act to fix the root cause)"]
    lines += [f"  {k}: {v}" for k, v in OWNERS.items()]
    lines += ["", "location: a JSON array of strings.", LOCATION_RULES, ""]
    lines += ["next_check: exactly one of (the single check that would decide the root cause "
              "if the documents do not; \"none\" if they do)"]
    lines += [f"  {k}: {v}" for k, v in CHECKS.items()]
    lines += ["",
              f"value: a JSON string holding {value_question}.", "",
              "Example of the format only (not a hint):",
              "```json",
              '{"cause": "file_too_large", "layer": "transport", "owner": "receiver", '
              '"location": ["SFID.SFIDFSIZ"], "next_check": "none", "value": "12345"}',
              "```"]
    return "\n".join(lines) + "\n"
