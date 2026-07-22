"""
Chart generation.
  - Pax/Flights: interactive Plotly figure (hover shows the exact number per
    bar — this is the one chart that needed real hover, per feedback).
  - Airlines / Cargo: matplotlib, returned as base64 PNGs, embedded in the
    custom HTML card grid in app.py (unchanged approach from before).

All functions take data as explicit parameters now rather than importing
data.py directly — the live values come from store.py (fetched or manually
edited), data.py is only the seed default.
"""
import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

BURGUNDY = "#7a1f2b"
BURGUNDY_LIGHT = "#b96b78"   # tint, used for "Outbound (Dom)" in cargo split
ACCENT = "#e28f96"           # lighter red — secondary series
ACCENT_LIGHT = "#f2cdd0"     # pale tint, used for "Inbound (Int)" in cargo split
GRID = "#eeeeee"
TEXT = "#333333"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 7,
    "text.color": TEXT,
    "axes.edgecolor": "#dddddd",
    "axes.labelcolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
})

DPI = 170


def _fig_to_base64(fig, dpi=DPI):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                pad_inches=0.03, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _fmt_exact(n):
    return f"{int(round(n)):,}"


# ------------------------------------------------------------ Pax/Flights ---
def pax_flights_figure(airports, mode, value_field_prefix, x_title):
    """Interactive horizontal bar chart with hover tooltips.
    airports: list of dicts with name + {prefix}_dom / {prefix}_intl-style
              keys (dom_pax/intl_pax or dom_flights/intl_flights).
    mode: 'Total' or 'Split'.
    value_field_prefix: 'pax' or 'flights'.
    """
    names = [a["name"] for a in airports]
    dom = [a[f"dom_{value_field_prefix}"] for a in airports]
    intl = [a[f"intl_{value_field_prefix}"] for a in airports]
    # reverse so the biggest ends up at the TOP of the horizontal chart
    names_r = names[::-1]
    dom_r = dom[::-1]
    intl_r = intl[::-1]

    fig = go.Figure()

    if mode == "Split":
        fig.add_trace(go.Bar(
            y=names_r, x=dom_r, name="Domestic", orientation="h",
            marker_color=BURGUNDY,
            hovertemplate="%{y}<br>Domestic: %{x:,}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            y=names_r, x=intl_r, name="International", orientation="h",
            marker_color=ACCENT,
            hovertemplate="%{y}<br>International: %{x:,}<extra></extra>",
        ))
        barmode = "group"
    else:
        total_r = [d + i for d, i in zip(dom_r, intl_r)]
        fig.add_trace(go.Bar(
            y=names_r, x=total_r, orientation="h",
            marker_color=BURGUNDY, showlegend=False,
            hovertemplate="%{y}<br>Total: %{x:,}<extra></extra>",
        ))
        barmode = "group"

    fig.update_layout(
        barmode=barmode,
        margin=dict(l=4, r=12, t=4, b=4),
        height=460,
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color=TEXT, family="sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="right", x=1, font=dict(size=10)),
        hoverlabel=dict(bgcolor="white", font_size=12,
                         bordercolor=BURGUNDY, font_color=TEXT),
        bargap=0.28, bargroupgap=0.12,
    )
    fig.update_xaxes(title=None, showgrid=True, gridcolor=GRID,
                      tickfont=dict(size=9), rangemode="tozero")
    fig.update_yaxes(title=None, tickfont=dict(size=9), automargin=True)
    return fig


# --------------------------------------------------------------- Airlines ---
def airlines_chart(airlines, day1_label, day2_label, figsize=(4.6, 2.5)):
    names = [a["name"] for a in airlines]
    day1 = np.array([a["day1"] for a in airlines]) * 100
    day2 = np.array([a["day2"] for a in airlines]) * 100
    x = np.arange(len(names))
    w = 0.36

    fig, ax = plt.subplots(figsize=figsize)
    b1 = ax.bar(x - w/2, day1, width=w, color=BURGUNDY, label=day1_label)
    b2 = ax.bar(x + w/2, day2, width=w, color=ACCENT, label=day2_label)
    ax.bar_label(b1, fmt="%.0f%%", fontsize=5.6, padding=1)
    ax.bar_label(b2, fmt="%.0f%%", fontsize=5.6, padding=1)

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=6.4)
    ax.set_ylim(0, 112)
    ax.set_yticks([])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2,
              frameon=False, fontsize=6.2)
    fig.tight_layout(pad=0.2)
    return _fig_to_base64(fig)


# ------------------------------------------------------------------ Cargo ---
def cargo_chart(cargo, mode, figsize=(3.3, 2.2)):
    """cargo: dict with outbound_int, inbound_int, outbound_dom, inbound_dom
    (matches civilaviation.gov.in's own terminology)."""
    fig, ax = plt.subplots(figsize=figsize)

    if mode == "Split":
        labels = ["Outbound\n(Int)", "Inbound\n(Int)", "Outbound\n(Dom)", "Inbound\n(Dom)"]
        values = [cargo["outbound_int"], cargo["inbound_int"],
                  cargo["outbound_dom"], cargo["inbound_dom"]]
        colors = [ACCENT, ACCENT_LIGHT, BURGUNDY, BURGUNDY_LIGHT]
        x = np.arange(4)
        bars = ax.bar(x, values, width=0.6, color=colors, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=6.0)

        ymax = max(values) * 1.42
        ax.set_ylim(0, ymax)
        ax.axvspan(-0.5, 1.5, color=ACCENT_LIGHT, alpha=0.15, zorder=0)
        ax.axvspan(1.5, 3.5, color=BURGUNDY_LIGHT, alpha=0.15, zorder=0)
        ax.axvline(1.5, color="#ccc", linewidth=0.8, zorder=1)
        ax.text(0.5, ymax * 0.94, "INTERNATIONAL", ha="center", va="top",
                fontsize=6.3, fontweight="bold", color=ACCENT)
        ax.text(2.5, ymax * 0.94, "DOMESTIC", ha="center", va="top",
                fontsize=6.3, fontweight="bold", color=BURGUNDY)
    else:
        intl_total = cargo["outbound_int"] + cargo["inbound_int"]
        dom_total = cargo["outbound_dom"] + cargo["inbound_dom"]
        labels = ["International", "Domestic"]
        values = [intl_total, dom_total]
        colors = [ACCENT, BURGUNDY]
        x = np.arange(2)
        bars = ax.bar(x, values, width=0.45, color=colors)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=6.8)

    ax.bar_label(bars, fmt="%d MT", fontsize=6.2, padding=2)
    ax.set_yticks([])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.margins(y=0.15)
    fig.tight_layout(pad=0.2)
    return _fig_to_base64(fig)
