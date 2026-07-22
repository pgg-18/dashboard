"""
Scrapes https://www.civilaviation.gov.in/ for the sections that have a live,
directly-fetchable equivalent: Airlines On-Time Performance, Cargo, UDAN,
Airport counts, Air Sewa Grievance, Skilling by IGRUA, Skilling by RGNAU.

There is NO per-airport Pax/Flights breakdown on this page (only nationwide
totals) — that section stays manual-only, by design (see app.py).

IMPORTANT / UNTESTED CAVEAT: this was built by inspecting one fetch of the
live page's rendered text, not the raw HTML — I don't have network access to
civilaviation.gov.in from my build environment to test this end-to-end. The
parser uses a fairly general heuristic (grouping consecutive Hindi-label /
English-label / value / [note] text, since that pattern was consistent
across every section observed) rather than exact CSS-class selectors, which
should be more resistant to markup changes, but hasn't been run against the
live site. If a "Fetch" button errors or returns wrong values, that's the
first place to look — please report back exactly what happened so this can
be fixed against the real page.

Every fetch function raises FetchError with a clear message on failure
rather than returning partial/wrong data — callers must leave the existing
stored value untouched if this raises.
"""
import re
import unicodedata

import requests
from bs4 import BeautifulSoup

URL = "https://www.civilaviation.gov.in/"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AAIDashboard/1.0)"}

MONTHS = {
    "january": "Jan", "february": "Feb", "march": "Mar", "april": "Apr",
    "may": "May", "june": "Jun", "july": "Jul", "august": "Aug",
    "september": "Sep", "october": "Oct", "november": "Nov", "december": "Dec",
}


class FetchError(Exception):
    pass


def _get_soup():
    try:
        resp = requests.get(URL, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"Could not reach {URL}: {e}")
    return BeautifulSoup(resp.text, "html.parser")


def _is_devanagari(s):
    return any("DEVANAGARI" in unicodedata.name(ch, "") for ch in s if ch.strip())


def _reformat_date(raw):
    """'20 July 2026' -> '20 Jul 2026'. Returns raw unchanged if it doesn't match."""
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw)
    if not m:
        return raw.strip()
    day, month, year = m.groups()
    abbr = MONTHS.get(month.lower(), month[:3].title())
    return f"{day} {abbr} {year}"


def _section_text_block(soup, heading_predicate):
    """Find an h2 whose text satisfies heading_predicate, and return the
    stripped strings from that heading up to (not including) the next h2."""
    headings = soup.find_all(["h2"])
    for idx, h in enumerate(headings):
        if heading_predicate(h.get_text(" ", strip=True)):
            texts = []
            for el in h.find_all_next():
                if el.name == "h2":
                    break
                if el.string and el.string.strip():
                    texts.append(el.string.strip())
            if len(texts) < 4:
                sib = h.find_next_sibling()
                texts = []
                while sib and sib.name != "h2":
                    texts.extend(list(sib.stripped_strings))
                    sib = sib.find_next_sibling()
            return texts
    return None


def _parse_items(texts):
    """Group a flat list of strings into (english_label, value, note) triples
    using the consistent [hindi, english, value, (note)] pattern observed on
    every section of the page."""
    items = []
    i = 0
    n = len(texts)
    while i < n:
        if _is_devanagari(texts[i]):
            i += 1
            english = texts[i] if i < n else None
            i += 1
            value = texts[i] if i < n else None
            i += 1
            note = None
            if i < n and not _is_devanagari(texts[i]) and texts[i] != english:
                if not re.match(r"^(On|Till)\s+\d", texts[i]):
                    note = texts[i]
                    i += 1
            # Some sections render "VALUE (note text)" as a SINGLE text node
            # rather than two separate ones (this is what happened with
            # RGNAU's "Number of courses" on the real site — the note ended
            # up jammed into the value, showing as the box's big number).
            # If we didn't already capture a separate note, and the value
            # itself contains a parenthetical, split it out here.
            if value and note is None and "(" in value:
                value, _, rest = value.partition("(")
                value = value.strip()
                note = rest.rstrip(") ").strip() or None
            if english and value:
                items.append((english.strip(), value.strip(), note))
        else:
            i += 1
    return items


def _find(items, *keywords, exact=False):
    for label, value, note in items:
        low = label.lower().strip()
        if exact:
            if low == keywords[0]:
                return value, note
        elif all(kw in low for kw in keywords):
            return value, note
    return None, None


def _as_int(s):
    if s is None:
        return None
    cleaned = re.sub(r"[^\d]", "", s)
    if not cleaned:
        return None
    return int(cleaned)


def _clean_num_str(s):
    """Strip leading zeros off plain integers ('09' -> '9'); leave anything
    else (percentages, 'Lakhs', currency) untouched."""
    if s and s.strip().isdigit():
        return str(int(s.strip()))
    return s.strip() if s else s


def _section_date(texts):
    for t in texts[:3]:
        if re.match(r"^(On|Till)\s+\d", t):
            prefix, _, rest = t.partition(" ")
            return f"{prefix} {_reformat_date(rest)}"
    return None


# ------------------------------------------------------------------------- #
def fetch_airlines():
    soup = _get_soup()
    texts = _section_text_block(soup, lambda h: "On Time Performance" in h)
    if not texts:
        raise FetchError("Couldn't find the 'On Time Performance' section on the page.")
    items = _parse_items(texts)
    as_of = _section_date(texts)

    canonical = ["IndiGo", "Air India", "SpiceJet", "Air India Express",
                 "Alliance Air", "Akasa Air"]
    result = []
    for name in canonical:
        for label, value, _ in items:
            if label.strip().lower() == name.lower():
                pct = re.search(r"[\d.]+", value)
                if pct:
                    result.append({"name": name, "pct": float(pct.group()) / 100})
                break
    if not result:
        raise FetchError("Found the On-Time-Performance section but no airline rows parsed out of it.")
    return result, as_of


def fetch_cargo():
    soup = _get_soup()
    texts = _section_text_block(soup, lambda h: "Cargo (In MT)" in h or "Cargo (In" in h)
    if not texts:
        raise FetchError("Couldn't find the 'Cargo (In MT)' section on the page.")
    items = _parse_items(texts)
    as_of = _section_date(texts)

    outbound_int, _ = _find(items, "outbound", "int")
    inbound_int, _ = _find(items, "inbound", "int")
    outbound_dom, _ = _find(items, "outbound", "dom")
    inbound_dom, _ = _find(items, "inbound", "dom")
    vals = [outbound_int, inbound_int, outbound_dom, inbound_dom]
    if any(v is None for v in vals):
        raise FetchError(f"Cargo section found but some fields didn't parse: "
                          f"outbound_int={outbound_int}, inbound_int={inbound_int}, "
                          f"outbound_dom={outbound_dom}, inbound_dom={inbound_dom}")
    cargo = {
        "outbound_int": _as_int(outbound_int),
        "inbound_int": _as_int(inbound_int),
        "outbound_dom": _as_int(outbound_dom),
        "inbound_dom": _as_int(inbound_dom),
    }
    return cargo, as_of


def fetch_udan():
    soup = _get_soup()
    texts = _section_text_block(soup, lambda h: "UDAN (RCS)" in h)
    if not texts:
        raise FetchError("Couldn't find the 'UDAN (RCS)' section on the page.")
    items = _parse_items(texts)
    as_of = _section_date(texts)

    airports, airports_note = _find(items, "airport")
    routes, _ = _find(items, "route")
    operators, _ = _find(items, "operator")
    flights, _ = _find(items, "flight")
    passengers, _ = _find(items, "passenger")
    vgf, _ = _find(items, "viability")
    if not all([airports, routes, operators, flights, passengers, vgf]):
        raise FetchError(f"UDAN section found but some fields didn't parse: "
                          f"airports={airports}, routes={routes}, operators={operators}, "
                          f"flights={flights}, passengers={passengers}, vgf={vgf}")
    udan = {
        "Airports": _clean_num_str(airports),
        "Airports_note": (airports_note or "").strip("() ").strip() or None,
        "Routes": _clean_num_str(routes),
        "Operators": _clean_num_str(operators),
        "Flights": flights.strip(),
        "Passengers": passengers.strip(),
        "Viability Gap Funding": vgf.strip(),
    }
    return udan, as_of


def fetch_airport_counts():
    soup = _get_soup()
    texts = _section_text_block(
        soup,
        lambda h: h.strip() in ("Airports", "हवाईअड्डे Airports") or h.strip().endswith(" Airports"),
    )
    if not texts:
        raise FetchError("Couldn't find the 'Airports' (by category) section on the page.")
    items = _parse_items(texts)
    as_of = _section_date(texts)

    operational, _ = _find(items, "operational")
    international = None
    for label, value, _ in items:
        if label.lower().strip().startswith("international"):
            international = value
            break
    custom, _ = _find(items, "custom")
    domestic, _ = _find(items, "domestic")
    joint_venture, _ = _find(items, "joint")
    state_govt, _ = _find(items, "state govt")
    vals = [operational, international, custom, domestic, joint_venture, state_govt]
    if any(v is None for v in vals):
        raise FetchError(f"Airports section found but some fields didn't parse: {vals}")
    counts = {
        "Operational": _as_int(operational),
        "International": _as_int(international),
        "Custom": _as_int(custom),
        "Domestic": _as_int(domestic),
        "Joint Venture": _as_int(joint_venture),
        "State Govt/Private": _as_int(state_govt),
    }
    return counts, as_of


def fetch_airsewa():
    soup = _get_soup()
    texts = _section_text_block(soup, lambda h: "by volume" in h.lower())
    if not texts:
        raise FetchError("Couldn't find the 'Air Sewa Grievances (by volume)' section.")
    items = _parse_items(texts)
    as_of = _section_date(texts)

    received, _ = _find(items, "received", exact=True)
    received_td, _ = _find(items, "received", "till")
    resolved, _ = _find(items, "resolved", exact=True)
    resolved_td, _ = _find(items, "resolved", "till")
    pending, _ = _find(items, "pending", exact=True)
    vals = [received, received_td, resolved, resolved_td, pending]
    if any(v is None for v in vals):
        raise FetchError(f"Air Sewa Grievance section found but some fields didn't parse: {vals}")
    airsewa = {
        "Received Today": _as_int(received),
        "Resolved Today": _as_int(resolved),
        "Received Till Date": _as_int(received_td),
        "Resolved Till Date": _as_int(resolved_td),
        "Pending": _as_int(pending),
    }
    return airsewa, as_of


def fetch_igrua():
    soup = _get_soup()
    texts = _section_text_block(soup, lambda h: "Skilling by IGRUA" in h)
    if not texts:
        raise FetchError("Couldn't find the 'Skilling by IGRUA' section.")
    items = _parse_items(texts)
    as_of = _section_date(texts)

    courses, _ = _find(items, "course")
    registered, _ = _find(items, "regist")
    passout, note = _find(items, "passout")
    if passout is None:
        passout, note = _find(items, "pass")
    flying, _ = _find(items, "flying")
    vals = [courses, registered, passout, flying]
    if any(v is None for v in vals):
        raise FetchError(f"IGRUA section found but some fields didn't parse: {vals}")
    igrua = {
        "Courses & Activities": _clean_num_str(courses),
        "Registered Students": registered.strip(),
        "Students Passed Out": passout.strip(),
        "Flying Hours": flying.strip(),
    }
    return igrua, as_of


def fetch_rgnau():
    soup = _get_soup()
    texts = _section_text_block(soup, lambda h: "Skilling by RGNAU" in h)
    if not texts:
        raise FetchError("Couldn't find the 'Skilling by RGNAU' section.")
    items = _parse_items(texts)
    as_of = _section_date(texts)

    courses, courses_note = _find(items, "number", "course")
    candidates, _ = _find(items, "number", "candidate")
    passed, _ = _find(items, "passed")
    jobs, _ = _find(items, "obtained", "job")
    vals = [courses, candidates, passed, jobs]
    if any(v is None for v in vals):
        raise FetchError(f"RGNAU section found but some fields didn't parse: {vals}")
    rgnau = {
        "Number of Courses": _clean_num_str(courses),
        "Number of Candidates": candidates.strip(),
        "Candidates Passed Out": passed.strip(),
        "Candidates Who Obtained Jobs": jobs.strip(),
    }
    note = None
    if courses_note:
        batches = re.search(r"(\d+)\s*\)?\s*$", courses_note.strip())
        if batches:
            note = f"{int(batches.group(1))} batches across {_clean_num_str(courses).zfill(2)} courses"
        else:
            note = courses_note
    return rgnau, note, as_of
