"""
AAI Daily Dashboard — single-screen, store-backed.

Run with:  streamlit run app.py
"""
import re

import pandas as pd
import streamlit as st

import charts as C
import data as D
import scraper
import store as ST

st.set_page_config(page_title="AAI Daily Dashboard", layout="wide",
                    initial_sidebar_state="collapsed")

BURGUNDY = C.BURGUNDY
ACCENT = C.ACCENT


def fmt_asof(label):
    if re.match(r"^(on|till)\s", label, re.IGNORECASE):
        return label[0].upper() + label[1:]
    return f"as on {label}"

# ---------------------------------------------------------------- CSS ----
st.markdown(f"""
<style>
    #MainMenu, footer, header {{visibility: hidden;}}
    /* Force strict single-screen behavior to prevent compression clipping */
    html, body, .stApp {{ overflow: hidden !important; height: 100vh; }}
    section[data-testid="stAppViewContainer"], .main {{ overflow: hidden !important; }}
    
    .block-container {{
        padding: 0.15rem 1rem 0.1rem 1rem !important; /* Tighter master padding */
        max-width: 100% !important;
    }}
    /* Heavily squash native Streamlit gaps */
    div[data-testid="stVerticalBlock"] {{ gap: 0.2rem !important; }}
    div[data-testid="stHorizontalBlock"] {{ gap: 0.5rem !important; }}

    .dash-title {{ font-size: 1.15rem; font-weight: 800; color: {BURGUNDY}; margin: 0; line-height: 1.2; }}
    .dash-sub {{ font-size: 0.68rem; color: #888; margin: 0; margin-bottom: 0.2rem; }}

    .card-head {{
        background: {BURGUNDY}; color: #fff; padding: 0.2rem 0.5rem;
        margin: -12px -12px 0 -12px; border-radius: 8px 8px 0 0;
    }}
    .card-title {{ font-size: 0.78rem; font-weight: 700; line-height: 1.2; color: #fff;
                   white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .card-date-line {{ font-size: 0.6rem; color: #999; line-height: 1.15; margin: 2px 0 0.2rem 2px; }}

    .hdr-row-marker {{ display: none; }}
    div[data-testid="stElementContainer"]:has(.hdr-row-marker) + div[data-testid="stLayoutWrapper"] div[data-testid="stHorizontalBlock"] {{
        background: {BURGUNDY}; border-radius: 8px 8px 0 0;
        margin: -12px -12px 0 -12px; align-items: center;
        padding: 0.15rem 0.5rem 0.15rem 0;
    }}
    div[data-testid="stElementContainer"]:has(.hdr-row-marker) + div[data-testid="stLayoutWrapper"] .card-title-wrap {{
        padding-left: 0.5rem; overflow: hidden;
    }}
    div[data-testid="stElementContainer"]:has(.hdr-row-marker) + div[data-testid="stLayoutWrapper"] div[data-testid="stButton"] {{
        display: flex; justify-content: flex-end;
    }}
    div[data-testid="stElementContainer"]:has(.hdr-row-marker) + div[data-testid="stLayoutWrapper"] div[data-testid="stButton"] button {{
        background: transparent !important; border: 1px solid rgba(255,255,255,0.55) !important;
        color: #fff !important; font-size: 0.6rem !important; padding: 0.08rem 0.4rem !important;
        min-height: 0 !important; white-space: nowrap !important;
    }}
    div[data-testid="stElementContainer"]:has(.hdr-row-marker) + div[data-testid="stLayoutWrapper"] div[data-testid="stButton"] button:hover {{
        background: rgba(255,255,255,0.2) !important; border-color: #fff !important;
    }}
    div[data-testid="stElementContainer"]:has(.hdr-row-marker) + div[data-testid="stLayoutWrapper"] div[data-testid="stButton"] button p {{
        white-space: nowrap !important;
    }}

    .stat-grid {{ display: grid; gap: 0.25rem; }}
    .stat-box {{
        border: 1px solid #ecdfe1; border-top: 3px solid {BURGUNDY};
        border-radius: 6px; background: #fdf9f9; overflow: hidden;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; padding: 0.15rem;
    }}
    .stat-val {{ font-size: 0.82rem; font-weight: 800; color: #222; line-height: 1.15; }}
    .stat-label {{ font-size: 0.55rem; color: #777; text-transform: uppercase;
                   letter-spacing: 0.02em; line-height: 1.2; margin-top: 1px; }}
    .stat-note {{ font-size: 0.46rem; color: #aaa; line-height: 1.05; margin-top: 1px; }}
    
    .chart-frame {{ width: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
    .chart-frame img {{ max-width: 100%; height: auto; display: block; }}

    div[role="radiogroup"] {{ gap: 0.4rem !important; flex-direction: row !important; }}
    div[role="radiogroup"] label {{ font-size: 0.7rem !important; }}

    div[data-testid="stButton"] button {{
        font-size: 0.68rem !important; padding: 0.15rem 0.55rem !important;
        min-height: 0 !important; border-color: {BURGUNDY} !important; color: {BURGUNDY} !important;
        white-space: nowrap !important;
    }}
    div[data-testid="stButton"] button:hover {{ background: {BURGUNDY} !important; color: #fff !important; }}
</style>
""", unsafe_allow_html=True)


def stat_boxes_html(items, cols, box_h_vh):
    boxes = ""
    for label, value, note in items:
        note_html = f'<div class="stat-note">{note}</div>' if note else ""
        boxes += (f'<div class="stat-box" style="height:{box_h_vh}vh;">'
                  f'<div class="stat-val">{value}</div>'
                  f'<div class="stat-label">{label}</div>{note_html}</div>')
    return f'<div class="stat-grid" style="grid-template-columns:repeat({cols},1fr);">{boxes}</div>'


def card_header(title, subtitle=None):
    st.markdown(f'<div class="card-head"><div class="card-title">{title}</div></div>',
                unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="card-date-line">{subtitle}</div>', unsafe_allow_html=True)


def card_header_with_button(title, subtitle, button_label, button_key, help_text=None):
    st.markdown('<span class="hdr-row-marker"></span>', unsafe_allow_html=True)
    hl, hr = st.columns([0.62, 0.38])
    with hl:
        st.markdown(f'<div class="card-title-wrap"><div class="card-title">{title}</div></div>',
                    unsafe_allow_html=True)
    with hr:
        clicked = st.button(button_label, key=button_key, help=help_text)
    if subtitle:
        st.markdown(f'<div class="card-date-line">{subtitle}</div>', unsafe_allow_html=True)
    return clicked


def handle_fetch(clicked, fetch_fn, on_success):
    if clicked:
        try:
            with st.spinner("Fetching..."):
                result = fetch_fn()
            on_success(result)
            st.rerun()
        except scraper.FetchError as e:
            st.error(f"Fetch failed: {e}")


# ------------------------------------------------------------- HEADER ----
store = ST.load()

st.markdown(f"""
<div class="dash-title">AAI Daily Dashboard</div>
<div class="dash-sub">Live sections pull from civilaviation.gov.in &nbsp;•&nbsp;
Pax &amp; Flights is manual-only (no per-airport figures on that page)</div>
""", unsafe_allow_html=True)

left, right = st.columns([0.4, 0.6], gap="medium")

# ============================================================ LEFT COL ===
with left:
    with st.container(border=True):
        clicked = card_header_with_button(
            "Passengers &amp; Flights — Top 20 Airports (by Total PAX)",
            fmt_asof(store['pax_flights_as_of']),
            "✎ Edit", "edit_pax_flights", help_text="Update manually")
        if clicked:
            st.session_state["show_pax_editor"] = True

        mode = st.radio("mode", ["Total", "Split"], horizontal=True,
                         label_visibility="collapsed", key="pax_mode")

        pax_fig = C.pax_flights_figure(store["top20_airports"], mode, "pax", "Passengers")
        flt_fig = C.pax_flights_figure(store["top20_airports"], mode, "flights", "Flights")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div style="text-align:center;font-size:0.7rem;font-weight:700;color:#888;margin:2px 0;">PAX</div>', unsafe_allow_html=True)
            st.plotly_chart(pax_fig, use_container_width=True, config={"displayModeBar": False}, key="pax_chart")
        with c2:
            st.markdown('<div style="text-align:center;font-size:0.7rem;font-weight:700;color:#888;margin:2px 0;">FLIGHTS</div>', unsafe_allow_html=True)
            st.plotly_chart(flt_fig, use_container_width=True, config={"displayModeBar": False}, key="flt_chart")

    with st.container(border=True):
        clicked = card_header_with_button("Skilling by IGRUA", store["igrua_as_of"],
                                           "⟳ Fetch", "fetch_igrua")
        handle_fetch(clicked, scraper.fetch_igrua,
                     lambda r: ST.update_many({"igrua": r[0], "igrua_as_of": r[1]}))
        items = [(k, v, None) for k, v in store["igrua"].items()]
        # Reduced vh
        st.markdown(stat_boxes_html(items, cols=2, box_h_vh=4.8), unsafe_allow_html=True)

# =========================================================== RIGHT COL ===
with right:
    r1a, r1b = st.columns([0.36, 0.64], gap="medium")
    with r1a:
        with st.container(border=True):
            clicked = card_header_with_button("Airports — by Category", store["airport_counts_as_of"],
                                               "⟳ Fetch", "fetch_airports")
            handle_fetch(clicked, scraper.fetch_airport_counts,
                         lambda r: ST.update_many({"airport_counts": r[0], "airport_counts_as_of": r[1]}))
            items = [(k, f"{v:,}", None) for k, v in store["airport_counts"].items()]
            # Reduced vh
            st.markdown(stat_boxes_html(items, cols=2, box_h_vh=4.2), unsafe_allow_html=True)
    with r1b:
        with st.container(border=True):
            clicked = card_header_with_button(
                "Airline On-Time Performance — 6 Metros", fmt_asof(store['airline_day1_label']),
                "⟳ Fetch", "fetch_airlines")
            handle_fetch(clicked, scraper.fetch_airlines,
                         lambda r: ST.update_many({
                             "airlines": [
                                 {"name": item["name"], "day1": item["pct"],
                                  "day2": next((o["day1"] for o in store["airlines"] if o["name"] == item["name"]), 0)}
                                 for item in r[0]
                             ],
                             "airline_day1_label": r[1] or "latest fetch",
                             "airline_day2_label": store["airline_day1_label"],
                         }))
            # Reduced height param in figsize
            air_img = C.airlines_chart(store["airlines"], store["airline_day1_label"],
                                        store["airline_day2_label"], figsize=(6.2, 1.5))
            st.markdown(f'<div class="chart-frame"><img src="data:image/png;base64,{air_img}"></div>',
                        unsafe_allow_html=True)

    r2a, r2b = st.columns([0.42, 0.58], gap="medium")
    with r2a:
        with st.container(border=True):
            clicked = card_header_with_button("Cargo Tonnage (MT)", store["cargo_as_of"],
                                               "⟳ Fetch", "fetch_cargo")
            handle_fetch(clicked, scraper.fetch_cargo,
                         lambda r: ST.update_many({"cargo": r[0], "cargo_as_of": r[1]}))
            cmode = st.radio("cmode", ["Total", "Split"], horizontal=True,
                              label_visibility="collapsed", key="cargo_mode")
            # Reduced height param in figsize
            cargo_img = C.cargo_chart(store["cargo"], cmode, figsize=(3.3, 1.15))
            st.markdown(f'<div class="chart-frame"><img src="data:image/png;base64,{cargo_img}"></div>',
                        unsafe_allow_html=True)
    with r2b:
        with st.container(border=True):
            clicked = card_header_with_button("UDAN (RCS)", store["udan_as_of"],
                                               "⟳ Fetch", "fetch_udan")
            handle_fetch(clicked, scraper.fetch_udan,
                         lambda r: ST.update_many({"udan": r[0], "udan_as_of": r[1]}))
            u = store["udan"]
            items = [
                ("Airports", u["Airports"], u.get("Airports_note")),
                ("Routes", u["Routes"], None),
                ("Operators", u["Operators"], None),
                ("Flights", u["Flights"], None),
                ("Passengers", u["Passengers"], None),
                ("Viability Gap Funding", u["Viability Gap Funding"], None),
            ]
            # Reduced vh
            st.markdown(stat_boxes_html(items, cols=3, box_h_vh=5.8), unsafe_allow_html=True)

    with st.container(border=True):
        clicked = card_header_with_button("Air Sewa Grievance", store["airsewa_as_of"],
                                           "⟳ Fetch", "fetch_airsewa")
        handle_fetch(clicked, scraper.fetch_airsewa,
                     lambda r: ST.update_many({"airsewa": r[0], "airsewa_as_of": r[1]}))
        items = [(k, f"{v:,}", None) for k, v in store["airsewa"].items()]
        # Reduced vh
        st.markdown(stat_boxes_html(items, cols=5, box_h_vh=3.8), unsafe_allow_html=True)

    with st.container(border=True):
        clicked = card_header_with_button("Skilling by RGNAU", store["rgnau_as_of"],
                                           "⟳ Fetch", "fetch_rgnau")
        handle_fetch(clicked, scraper.fetch_rgnau,
                     lambda r: ST.update_many({"rgnau": r[0], "rgnau_note": r[1], "rgnau_as_of": r[2]}))
        items = [(k, v, store["rgnau_note"] if k == "Number of Courses" else None)
                 for k, v in store["rgnau"].items()]
        # Reduced vh
        st.markdown(stat_boxes_html(items, cols=4, box_h_vh=4.8), unsafe_allow_html=True)


# ------------------------------------------------- MANUAL EDIT DIALOG ----
@st.dialog("Update Pax & Flights manually", width="large")
def pax_flights_editor():
    st.caption("Edit any cell. Add rows with the + at the bottom, delete with the row checkbox + trash icon. "
               "Rows are re-sorted by total PAX (domestic + international) on save.")
    df = pd.DataFrame(store["top20_airports"])
    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Airport", required=True),
            "dom_pax": st.column_config.NumberColumn("Domestic PAX", min_value=0, step=1),
            "intl_pax": st.column_config.NumberColumn("International PAX", min_value=0, step=1),
            "dom_flights": st.column_config.NumberColumn("Domestic Flights", min_value=0, step=1),
            "intl_flights": st.column_config.NumberColumn("International Flights", min_value=0, step=1),
        },
        key="pax_flights_data_editor",
    )
    as_of = st.text_input("As on / till date", value=store["pax_flights_as_of"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save", type="primary", use_container_width=True):
            records = edited.fillna(0).to_dict("records")
            records = [r for r in records if str(r.get("name", "")).strip()]
            for r in records:
                for k in ("dom_pax", "intl_pax", "dom_flights", "intl_flights"):
                    r[k] = int(r.get(k, 0) or 0)
                r["name"] = str(r["name"]).strip()
            records.sort(key=lambda r: -(r["dom_pax"] + r["intl_pax"]))
            ST.update_many({"top20_airports": records, "pax_flights_as_of": as_of.strip() or store["pax_flights_as_of"]})
            st.session_state["show_pax_editor"] = False
            st.rerun()
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_pax_editor"] = False
            st.rerun()


if st.session_state.get("show_pax_editor"):
    pax_flights_editor()
