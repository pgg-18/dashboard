"""
AAI Daily Dashboard — static, single-screen.

Run with:  streamlit run app.py

This build uses a hardcoded snapshot (data.py) from the datasheet supplied on
16 Jul 2026. There is no live scrape and no in-app upload yet — that refresh
mechanism was deferred; for now, updating the dashboard means editing data.py
with the next day's figures.

Layout notes:
  - Every "card" is ONE HTML string in a single st.markdown(...) call — a div
    opened in one call and closed in another does NOT nest in the rendered
    DOM (Streamlit isolates each markdown call), so radios/interactive
    widgets are kept OUTSIDE card HTML as their own elements.
  - Cards are sized by their CONTENT (fixed-pixel chart images, fixed-height
    stat boxes), not by a forced container height — an explicit height on
    .card was found to mismatch Streamlit's own wrapper sizing and caused
    cards to visually overlap their neighbours.

Layout mirrors the hand-drawn sketch:
  left column  -> Pax / Flights top-20-airport charts (+ Total/Split toggle),
                  Skilling by IGRUA underneath
  right column -> Airports + Airlines (top row)
                  Cargo (+ Total/Split toggle) + UDAN (middle row)
                  Air Sewa Grievance (strip)
                  Skilling by RGNAU (bottom)
"""
import re
import streamlit as st

import data as D
import charts as C


def _flat(html):
    """Collapse to a single line with no inter-tag whitespace. Streamlit's
    markdown parser treats a whitespace-only line inside an HTML block as a
    blank line, which ends 'raw HTML' mode — everything after it then gets
    re-parsed as markdown, and indented lines become a literal code block.
    Flattening avoids that failure mode entirely, regardless of content."""
    return re.sub(r">\s+<", "><", html.strip())

st.set_page_config(page_title="AAI Daily Dashboard", layout="wide",
                    initial_sidebar_state="collapsed")

BURGUNDY = C.BURGUNDY
ACCENT = C.ACCENT

# ---------------------------------------------------------------- CSS ----
st.markdown(f"""
<style>
    #MainMenu, footer, header {{visibility: hidden;}}
    html, body, .stApp {{ overflow: hidden !important; height: 100vh; }}
    section[data-testid="stAppViewContainer"], .main, .block-container {{
        overflow: hidden !important;
    }}
    .block-container {{
        padding: 0.2rem 1rem 0.1rem 1rem !important; /* Reduced master padding */
        max-width: 100% !important;
    }}
    
    /* Aggressively shrink Streamlit's default injected margins */
    div[data-testid="stVerticalBlock"] {{ gap: 0.4rem !important; }}
    div[data-testid="stHorizontalBlock"] {{ gap: 0.5rem !important; }}

    .dash-title {{ font-size: 1.25rem; font-weight: 800; color: {BURGUNDY}; margin: 0; line-height: 1.2; }}
    .dash-sub {{ font-size: 0.72rem; color: #888; margin: 0; margin-bottom: 0.2rem; }}

    .card {{ border: 1px solid #e4e4e4; border-radius: 10px; background: #fff; overflow: hidden; display: flex; flex-direction: column; }}
    
    /* Force the header to stack cleanly so dates don't get squished */
    .card-head {{ background: {BURGUNDY}; color: #fff; padding: 0.35rem 0.55rem; display: flex; flex-direction: column; justify-content: center; }}
    .card-title {{ font-size: 0.78rem; font-weight: 700; line-height: 1.2; }}
    .card-date  {{ font-size: 0.6rem; color: #f0dcdf; line-height: 1.2; margin-top: 0.15rem; }}
    
    .card-body {{ padding: 0.3rem 0.4rem; flex-grow: 1; }}
    .card-body.center {{ display: flex; justify-content: center; align-items: center; }}
    .card-body.two-img {{ display: flex; justify-content: center; gap: 0.25rem; align-items: center; }}

    .chart-frame {{ width: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
    .chart-frame img {{ max-width: 100%; max-height: 100%; width: auto; height: auto; display: block; }}

    .stat-grid {{ display: grid; gap: 0.28rem; }}
    .stat-box {{
        border: 1px solid #ecdfe1; border-top: 3px solid {BURGUNDY};
        border-radius: 6px; background: #fdf9f9; overflow: hidden;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; padding: 0.2rem; /* Added internal padding so text doesn't touch borders */
    }}
    
    /* Slightly scaled down typography to prevent text-wrap overflow inside smaller boxes */
    .stat-val {{ font-size: 0.82rem; font-weight: 800; color: #222; line-height: 1.15; }}
    .stat-label {{ font-size: 0.55rem; color: #777; text-transform: uppercase;
                   letter-spacing: 0.02em; line-height: 1.2; margin-top: 2px; }}
    .stat-note {{ font-size: 0.48rem; color: #aaa; line-height: 1.05; margin-top: 2px; }}

    .toggle-label {{ font-size: 0.66rem; color: #888; margin-bottom: -10px; text-transform: uppercase; }}
    div[role="radiogroup"] {{ gap: 0.5rem !important; flex-direction: row !important; }}
    div[role="radiogroup"] label {{ font-size: 0.72rem !important; }}
</style>
""", unsafe_allow_html=True)


def card_html(title, subtitle, body_inner, body_class="card-body"):
    date_html = f'<div class="card-date">{subtitle}</div>' if subtitle else ""
    return _flat(f"""<div class="card">
      <div class="card-head">
        <div class="card-title">{title}</div>
        {date_html}
      </div>
      <div class="{body_class}">{body_inner}</div>
    </div>""")


def img_tag(b64):
    return f'<img src="data:image/png;base64,{b64}">'


def chart_frame(b64, height_vh):
    return f'<div class="chart-frame" style="height:{height_vh}vh;">{img_tag(b64)}</div>'


def stat_boxes_html(items, cols, box_h_vh):
    boxes = ""
    for label, value, note in items:
        note_html = f'<div class="stat-note">{note}</div>' if note else ""
        boxes += f"""<div class="stat-box" style="height:{box_h_vh}vh;">
            <div class="stat-val">{value}</div>
            <div class="stat-label">{label}</div>
            {note_html}
        </div>"""
    return _flat(f'<div class="stat-grid" '
                 f'style="grid-template-columns:repeat({cols},1fr);">{boxes}</div>')


# ------------------------------------------------------------- HEADER ----
st.markdown(_flat(f"""
<div class="dash-title">AAI Daily Dashboard</div>
<div class="dash-sub">Data for {D.DATA_DATE} &nbsp;•&nbsp; published {D.PUBLISHED_DATE}
&nbsp;•&nbsp; Static snapshot — refresh by supplying the next datasheet</div>
"""), unsafe_allow_html=True)

left, right = st.columns([0.38, 0.62], gap="medium")

# ============================================================ LEFT COL ===
with left:
    st.markdown('<div class="toggle-label">View</div>', unsafe_allow_html=True)
    mode = st.radio("mode", ["Total", "Split"], horizontal=True,
                     label_visibility="collapsed", key="pax_mode")

    CHART_VH = 42  # Reduced from 46
    pax_b64 = C.pax_or_flights_chart("pax", mode, figsize=(3.2, 5.0))
    flt_b64 = C.pax_or_flights_chart("flights", mode, figsize=(3.2, 5.0))
    body = (f'<div class="chart-frame" style="height:{CHART_VH}vh;">{img_tag(pax_b64)}</div>'
            f'<div class="chart-frame" style="height:{CHART_VH}vh;">{img_tag(flt_b64)}</div>')
    st.markdown(card_html("Passengers &amp; Flights — Top 20 Airports (by Total PAX)",
                           "Left: Pax &nbsp;|&nbsp; Right: Flights",
                           body, "card-body two-img"), unsafe_allow_html=True)

    items = [(k, v, None) for k, v in D.IGRUA.items()]
    # Reduced box_h_vh from 6.5 to 5.5
    st.markdown(card_html("Skilling by IGRUA", D.IGRUA_AS_OF,
                           stat_boxes_html(items, cols=2, box_h_vh=5.5)), unsafe_allow_html=True)

# =========================================================== RIGHT COL ===
with right:
    r1a, r1b = st.columns([0.36, 0.64], gap="medium")
    with r1a:
        items = [(label, f'{v:,}', None) for label, v in D.AIRPORT_COUNTS.items()]
        # Reduced box_h_vh from 6 to 5.5
        st.markdown(card_html("Airports — by Category", None,
                               stat_boxes_html(items, cols=2, box_h_vh=5.5)), unsafe_allow_html=True)
    with r1b:
        air_b64 = C.airlines_chart(figsize=(6.4, 2.0))
        # Reduced frame from 20 to 18
        st.markdown(card_html("Airline On-Time Performance — 6 Metros", None,
                               chart_frame(air_b64, 18), "card-body center"),
                     unsafe_allow_html=True)

    r2a, r2b = st.columns([0.42, 0.58], gap="medium")
    with r2a:
        st.markdown('<div class="toggle-label">View</div>', unsafe_allow_html=True)
        cmode = st.radio("cmode", ["Total", "Split"], horizontal=True,
                          label_visibility="collapsed", key="cargo_mode")
        cargo_b64 = C.cargo_chart(cmode, figsize=(3.4, 1.7))
        # Reduced frame from 14 to 12
        st.markdown(card_html("Cargo Tonnage (MT)", "AAICLAS",
                               chart_frame(cargo_b64, 12), "card-body center"),
                     unsafe_allow_html=True)
    with r2b:
        items = [
            ("Airports", D.UDAN["Airports"], D.UDAN["Airports_note"]),
            ("Routes", D.UDAN["Routes"], None),
            ("Operators", D.UDAN["Operators"], None),
            ("Flights", D.UDAN["Flights"], None),
            ("Passengers", D.UDAN["Passengers"], None),
            ("Viability Gap Funding", D.UDAN["Viability Gap Funding"], None),
        ]
        # Reduced box_h_vh from 9.5 to 7.5
        st.markdown(card_html("UDAN (RCS)", D.UDAN_AS_OF,
                               stat_boxes_html(items, cols=3, box_h_vh=7.5)), unsafe_allow_html=True)

    items = [(k, f'{v:,}', None) for k, v in D.AIRSEWA.items()]
    # Reduced box_h_vh from 6.5 to 5.5
    st.markdown(card_html("Air Sewa Grievance", D.DATA_DATE,
                           stat_boxes_html(items, cols=5, box_h_vh=5.5)), unsafe_allow_html=True)

    items = [(k, v, D.RGNAU_NOTE if k == "Number of Courses" else None)
             for k, v in D.RGNAU.items()]
    # Reduced box_h_vh from 7.5 to 6.5
    st.markdown(card_html("Skilling by RGNAU", D.RGNAU_AS_OF,
                           stat_boxes_html(items, cols=4, box_h_vh=6.5)), unsafe_allow_html=True)
