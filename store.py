"""
Persistence for the dashboard. Every editable section (fetched or manually
updated) lives in a single JSON file on disk, seeded from data.py's DEFAULTS
the first time the app runs. This mirrors the previous dashboard's store.py.

CAVEAT: on Streamlit Community Cloud the filesystem is NOT guaranteed to
survive a redeploy (only reruns/reboots of the same running instance) — same
limitation the earlier dashboard had. Fetched/edited data can disappear after
a redeploy; there's no fix for that without external storage.
"""
import json
import os
import copy

import data as D

STORE_PATH = os.path.join(os.path.dirname(__file__), "dashboard_store.json")

DEFAULTS = {
    "top20_airports": D.TOP20_AIRPORTS,
    "pax_flights_as_of": D.DATA_DATE,
    "airport_counts": D.AIRPORT_COUNTS,
    "airport_counts_as_of": D.AIRPORT_COUNTS_AS_OF,
    "airlines": D.AIRLINES,
    "airline_day1_label": D.AIRLINE_DAY1_LABEL,
    "airline_day2_label": D.AIRLINE_DAY2_LABEL,
    "cargo": D.CARGO,
    "cargo_as_of": D.CARGO_AS_OF,
    "udan": D.UDAN,
    "udan_as_of": D.UDAN_AS_OF,
    "igrua": D.IGRUA,
    "igrua_as_of": D.IGRUA_AS_OF,
    "rgnau": D.RGNAU,
    "rgnau_note": D.RGNAU_NOTE,
    "rgnau_as_of": D.RGNAU_AS_OF,
    "airsewa": D.AIRSEWA,
    "airsewa_as_of": D.DATA_DATE,
}


def _load_raw():
    if not os.path.exists(STORE_PATH):
        save(copy.deepcopy(DEFAULTS))
    with open(STORE_PATH, "r") as f:
        return json.load(f)


def save(store):
    with open(STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)


def load():
    """Returns the full store, filling in any missing keys from DEFAULTS
    (so adding a new section to DEFAULTS later doesn't break an existing
    store.json on disk)."""
    store = _load_raw()
    changed = False
    for k, v in DEFAULTS.items():
        if k not in store:
            store[k] = copy.deepcopy(v)
            changed = True
    if changed:
        save(store)
    return store


def update_section(section, value, as_of_key=None, as_of_value=None):
    """Overwrite one section (and optionally its as-of date), persist, return
    the updated store."""
    store = load()
    store[section] = value
    if as_of_key:
        store[as_of_key] = as_of_value
    save(store)
    return store


def update_many(updates: dict):
    """Overwrite several keys at once, persist, return the updated store."""
    store = load()
    store.update(updates)
    save(store)
    return store


def reset_to_defaults():
    save(copy.deepcopy(DEFAULTS))
    return load()
