# AAI Daily Dashboard

A static, single-screen Streamlit dashboard built from the AAI daily datasheet
(15 Jul 2026 data, published 16 Jul 2026). Same colour theme as the earlier
Civil Aviation dashboard: burgundy card headers with white text, gold as the
one accent colour, everything else burgundy/neutral.

## Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501

## Files
- `app.py`   – the Streamlit UI: layout, cards, radio toggles
- `charts.py` – matplotlib chart generation (returns base64 PNGs)
- `data.py`  – all figures, hardcoded from the datasheet you supplied
- `requirements.txt`

## What's on it
- **Passengers & Flights** — top 20 airports by domestic PAX, with a
  Total/Split toggle (Split breaks each bar into Domestic vs International).
  The **Flights** panel next to it is a placeholder — same layout/format,
  bars fixed at 0 — because the sheet has no per-airport flight counts yet.
  Swap in real numbers in `data.py` (`TOP20_AIRPORTS`, the `dom_flights` /
  `intl_flights` keys) whenever that data's ready and it'll render like the
  Pax panel automatically.
- **Airports** — nationwide Domestic vs International departure PAX.
- **Airline On-Time Performance** — 5 airlines with day-over-day bars.
  Air India Express is left out because it had no figures for this date;
  the chart only plots airlines that have data that day (see `AIRLINES` in
  `data.py` — add a row back in and it reappears).
- **Cargo Tonnage** — Total/Split toggle (Total = International vs
  Domestic; Split = Export/Import vs Outbound/Inbound).
- **UDAN (RCS)**, **Air Sewa Grievance**, **Skilling by IGRUA**,
  **Skilling by RGNAU** — stat-box cards straight from the sheet.

## Static by design
This is a **hardcoded snapshot**, same static philosophy as the last
dashboard — no live scrape, no upload button (that refresh mechanism was
explicitly deferred). To update it for a new day: open `data.py` and replace
the values with the next datasheet's figures. If a daily-refresh workflow
(upload button, or you sending me the next file) is wanted later, that's a
straightforward follow-on.

## A couple of build notes, in case you edit this yourself
- Every "card" is built as **one single HTML string** in a single
  `st.markdown(..., unsafe_allow_html=True)` call. Streamlit renders each
  markdown call as an isolated fragment — splitting a card's opening and
  closing tags across two calls (e.g. to slot a widget in between) causes
  the browser to silently auto-close the div, breaking the card border.
  Radio buttons are kept as separate elements outside the card HTML for
  this reason.
- HTML strings are flattened to a single line (`_flat()` in `app.py`)
  before being handed to `st.markdown`. A blank/whitespace-only line inside
  a multi-line HTML string makes Streamlit's markdown parser drop out of
  "raw HTML" mode partway through and start rendering literal `<div>` text —
  flattening sidesteps that entirely.
