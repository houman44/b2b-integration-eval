"""EDIFACT helpers for the translation tasks: escaping, segment splitting."""

SPECIAL = "?+:'"


def esc(text: str) -> str:
    """Release character '?' before each service character (UNA defaults)."""
    return "".join("?" + c if c in SPECIAL else c for c in text)


def split_segments(text: str):
    """Split an interchange on unescaped segment terminators. Line breaks
    between segments are ignored."""
    text = text.replace("\r", "").replace("\n", "")
    segs, cur, i = [], [], 0
    while i < len(text):
        c = text[i]
        if c == "?" and i + 1 < len(text):
            cur.append(text[i:i + 2])
            i += 2
            continue
        if c == "'":
            segs.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if "".join(cur).strip():
        segs.append("".join(cur).strip())
    return [s for s in segs if s]


def split_elements(seg: str):
    """Split a segment into elements and components, honouring '?'."""
    out, cur_el, cur_comp, i = [], [], [], 0
    while i < len(seg):
        c = seg[i]
        if c == "?" and i + 1 < len(seg):
            cur_comp.append(seg[i + 1])
            i += 2
            continue
        if c == "+":
            cur_el.append("".join(cur_comp)); out.append(cur_el); cur_el, cur_comp = [], []
        elif c == ":":
            cur_el.append("".join(cur_comp)); cur_comp = []
        else:
            cur_comp.append(c)
        i += 1
    cur_el.append("".join(cur_comp)); out.append(cur_el)
    return out


def transliterate_unoa(text: str) -> str:
    """The mapping spec's UNOC-to-UNOA rule (written for this eval)."""
    table = {"Ä": "AE", "Ö": "OE", "Ü": "UE", "ä": "AE", "ö": "OE", "ü": "UE", "ß": "SS",
             "É": "E", "é": "E", "È": "E", "è": "E", "Å": "A", "å": "A", "Ø": "O", "ø": "O"}
    return "".join(table.get(c, c) for c in text).upper()


def fmt_decimal(cents_like: int, places: int) -> str:
    """Integer with implied decimals -> shortest EDIFACT decimal ('.' mark):
    no trailing zeros, no decimal point for whole numbers."""
    neg = cents_like < 0
    v = abs(cents_like)
    whole, frac = divmod(v, 10 ** places)
    s = str(whole)
    if frac:
        s += "." + f"{frac:0{places}d}".rstrip("0")
    return ("-" if neg else "") + s
