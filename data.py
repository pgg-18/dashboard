"""
Seed defaults for the dashboard, hardcoded from:
  DAILY_DATASHEET_16_JULY_2026_UPDATED_9587.xlsx  ("Dashboard" sheet, cross-checked
  against the "Data" sheet). Traffic/cargo/airline/grievance figures are for
  15 Jul 2026 (published 16 Jul 2026). UDAN is cumulative till 30 Jun 2026.
  IGRUA is cumulative till 03 Jul 2026. RGNAU is cumulative till 08 Jul 2026.
  Airport counts cross-checked live against civilaviation.gov.in, till 07 Jul 2026.

These are SEED values only — store.py loads them into dashboard_store.json on
first run. After that, the live dashboard state lives in the JSON file, kept
up to date via each section's "Fetch" button (scraper.py, pulling from
civilaviation.gov.in) or, for Pax & Flights, the "Update Manually" editor —
there's no per-airport data on the live site, so that section is manual-only.
"""

DATA_DATE = "15 Jul 2026"
PUBLISHED_DATE = "16 Jul 2026"

# --- Top 20 airports, ranked by TOTAL PAX (domestic + international) descending.
# NOTE: this list was previously sorted by domestic PAX only (matching the
# source sheet's own pre-sort), which put Bengaluru (44,815 domestic) above
# Mumbai (43,193 domestic) even though Mumbai's total — thanks to its much
# larger international traffic (18,332 vs Bengaluru's 8,767) — is actually
# higher: 61,525 vs 53,582. Re-sorted by total so the visual order always
# matches what "Total" mode displays (and Split mode keeps the same order).
TOP20_AIRPORTS = [
    {"name": "Delhi",        "dom_pax": 74016, "intl_pax": 26529, "dom_flights": 446, "intl_flights": 138},  # total 100,545
    {"name": "Mumbai",       "dom_pax": 43193, "intl_pax": 18332, "dom_flights": 267, "intl_flights": 105},  # total 61,525
    {"name": "Bengaluru",    "dom_pax": 44815, "intl_pax": 8767,  "dom_flights": 265, "intl_flights": 48},   # total 53,582
    {"name": "Hyderabad",    "dom_pax": 28616, "intl_pax": 6992,  "dom_flights": 180, "intl_flights": 39},   # total 35,608
    {"name": "Chennai",      "dom_pax": 18917, "intl_pax": 7227,  "dom_flights": 116, "intl_flights": 41},   # total 26,144
    {"name": "Kolkata",      "dom_pax": 21971, "intl_pax": 2559,  "dom_flights": 126, "intl_flights": 18},   # total 24,530
    {"name": "Pune",         "dom_pax": 15858, "intl_pax": 110,   "dom_flights": 101, "intl_flights": 1},    # total 15,968
    {"name": "Ahmedabad",    "dom_pax": 10990, "intl_pax": 2445,  "dom_flights": 72,  "intl_flights": 15},   # total 13,435
    {"name": "Kochi",        "dom_pax": 6573,  "intl_pax": 6600,  "dom_flights": 48,  "intl_flights": 42},   # total 13,173
    {"name": "Guwahati",     "dom_pax": 8567,  "intl_pax": 72,    "dom_flights": 53,  "intl_flights": 1},    # total 8,639
    {"name": "Lucknow",      "dom_pax": 5515,  "intl_pax": 1199,  "dom_flights": 35,  "intl_flights": 8},    # total 6,714
    {"name": "Goa (Dabolim)","dom_pax": 6170,  "intl_pax": 75,    "dom_flights": 36,  "intl_flights": 1},    # total 6,245
    {"name": "Navi Mumbai",  "dom_pax": 6127,  "intl_pax": 83,    "dom_flights": 46,  "intl_flights": 1},    # total 6,210
    {"name": "Bagdogra",     "dom_pax": 5604,  "intl_pax": 0,     "dom_flights": 32,  "intl_flights": 0},    # total 5,604
    {"name": "Jaipur",       "dom_pax": 5149,  "intl_pax": 449,   "dom_flights": 37,  "intl_flights": 3},    # total 5,598
    {"name": "Srinagar",     "dom_pax": 5526,  "intl_pax": 0,     "dom_flights": 34,  "intl_flights": 0},    # total 5,526
    {"name": "Chandigarh",   "dom_pax": 4690,  "intl_pax": 167,   "dom_flights": 31,  "intl_flights": 1},    # total 4,857
    {"name": "Indore",       "dom_pax": 4725,  "intl_pax": 89,    "dom_flights": 32,  "intl_flights": 1},    # total 4,814
    {"name": "Bhubaneswar",  "dom_pax": 4645,  "intl_pax": 0,     "dom_flights": 38,  "intl_flights": 0},    # total 4,645
    {"name": "Patna",        "dom_pax": 4487,  "intl_pax": 0,     "dom_flights": 31,  "intl_flights": 0},    # total 4,487
]

# --- Airport count breakdown by category, cross-checked live 21 Jul 2026 ---
AIRPORT_COUNTS = {
    "Operational": 165,
    "International": 36,
    "Custom": 11,
    "Domestic": 118,
    "Joint Venture": 9,
    "State Govt/Private": 30,
}
AIRPORT_COUNTS_AS_OF = "till 07 Jul 2026"

# --- Airline on-time performance, 6 metros. Airlines with no data that day are
#     simply left out (e.g. Air India Express had no figures on 15 Jul 2026).
#     "day1" is the most recent fetch, "day2" the one before it — each Fetch
#     shifts day1 -> day2 and inserts the newly scraped value as day1. ---
AIRLINES = [
    {"name": "IndiGo",       "day1": 0.9420, "day2": 0.9720},
    {"name": "Air India",    "day1": 0.9118, "day2": 0.9349},
    {"name": "SpiceJet",     "day1": 0.5770, "day2": 0.5000},
    {"name": "Alliance Air", "day1": 0.8300, "day2": 0.9300},
    {"name": "Akasa Air",    "day1": 0.9651, "day2": 0.9750},
]
AIRLINE_DAY1_LABEL = "15 Jul 2026"
AIRLINE_DAY2_LABEL = "14 Jul 2026"

# --- Cargo tonnage (MT). Field names match the live site's own terminology
# (civilaviation.gov.in uses Outbound/Inbound x International/Domestic, not
# Export/Import) so the "Fetch" mapping is a direct 1:1, no reinterpretation. ---
CARGO = {
    "outbound_int": 441,  # was "export"
    "inbound_int": 118,   # was "import"
    "outbound_dom": 37,
    "inbound_dom": 68,
}
CARGO_AS_OF = "15 Jul 2026"

# --- UDAN (RCS), cumulative till 30 Jun 2026 ---
UDAN = {
    "Airports": "95",
    "Airports_note": "incl. 17 heliports, 2 water aerodromes",
    "Routes": "677",
    "Operators": "9",
    "Flights": "3.58 Lakhs",
    "Passengers": "168 Lakhs",
    "Viability Gap Funding": "INR 4,881.10 Cr",
}
UDAN_AS_OF = "till 30 Jun 2026"

# --- Skilling by IGRUA, cumulative till 03 Jul 2026 ---
IGRUA = {
    "Courses & Activities": "16",
    "Registered Students": "2,169",
    "Students Passed Out": "1,792",
    "Flying Hours": "3,80,352:40",
}
IGRUA_AS_OF = "till 03 Jul 2026"

# --- Skilling by RGNAU, cumulative till 08 Jul 2026 ---
RGNAU = {
    "Number of Courses": "8",
    "Number of Candidates": "1,508",
    "Candidates Passed Out": "1,037",
    "Candidates Who Obtained Jobs": "940",
}
RGNAU_NOTE = "41 batches across 08 courses"
RGNAU_AS_OF = "till 08 Jul 2026"

# --- Air Sewa Grievance ---
AIRSEWA = {
    "Received Today": 112,
    "Resolved Today": 136,
    "Received Till Date": 176467,
    "Resolved Till Date": 176074,
    "Pending": 393,
}
