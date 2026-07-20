"""
Chart generation. All charts are rendered with matplotlib and returned as
base64 PNGs so they can be dropped straight into the custom HTML grid in app.py.

Colour theme (matches the previous dashboard):
  BURGUNDY = card headers / "domestic" series / primary accent
  ACCENT   = "international" series / secondary accent — a lighter red,
             the one extra accent colour, per "small accent palette, rest
             everything burgundy"
"""
import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import data as D

BURGUNDY = "#7a1f2b"
BURGUNDY_LIGHT = "#b96b78"   # tint, used for "Outbound" in cargo split
ACCENT = "#e28f96"           # lighter red — secondary series (lightened per feedback)
ACCENT_LIGHT = "#f2cdd0"     # pale tint, used for "Import" in cargo split
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


DPI = 170  # exported so app.py can compute exact pixel dims for <img width/height>


def _fig_to_base64(fig, dpi=DPI):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                pad_inches=0.03, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _fmt_k(n):
    if n >= 1000:
        return f"{n/1000:.0f}k"
    return str(n)


def _fmt_exact(n):
    return f"{int(round(n)):,}"


def pax_or_flights_chart(field_prefix, mode, figsize=(3.6, 3.55)):
    """field_prefix: 'pax' or 'flights'. mode: 'Total' or 'Split'."""
    airports = D.TOP20_AIRPORTS
    names = [a["name"] for a in airports]
    dom = np.array([a[f"dom_{field_prefix}"] for a in airports], dtype=float)
    intl = np.array([a[f"intl_{field_prefix}"] for a in airports], dtype=float)
    y = np.arange(len(names))[::-1]  # top of list at top of chart

    fig, ax = plt.subplots(figsize=figsize)

    if mode == "Split":
        h = 0.38
        bars_dom = ax.barh(y + h/2, dom, height=h, color=BURGUNDY, label="Domestic", zorder=3)
        bars_intl = ax.barh(y - h/2, intl, height=h, color=ACCENT, label="International", zorder=3)
        ax.bar_label(bars_dom, labels=[_fmt_exact(v) for v in dom], fontsize=4.8, padding=2)
        ax.bar_label(bars_intl, labels=[_fmt_exact(v) for v in intl], fontsize=4.8, padding=2)
        ax.legend(loc="lower right", frameon=False, fontsize=6, ncol=1)
        ax.margins(x=0.18)  # headroom so labels on the longest bars aren't clipped
    else:
        total = dom + intl
        bars = ax.barh(y, total, height=0.55, color=BURGUNDY, zorder=3)
        ax.bar_label(bars, labels=[_fmt_exact(v) for v in total], fontsize=5.2, padding=2)
        ax.margins(x=0.14)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=6.3)
    ax.tick_params(axis="x", labelsize=6)
    if (dom + intl).max() == 0:
        # placeholder chart (no per-airport flight data yet): fixed clean axis
        ax.set_xlim(0, 10)
        ax.set_xticks([0, 2, 4, 6, 8, 10])
    else:
        ax.xaxis.set_major_formatter(lambda v, pos: _fmt_k(v))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout(pad=0.2)
    return _fig_to_base64(fig)


def airlines_chart(figsize=(4.6, 2.5)):
    airlines = D.AIRLINES
    names = [a["name"] for a in airlines]
    day1 = np.array([a["day1"] for a in airlines]) * 100
    day2 = np.array([a["day2"] for a in airlines]) * 100
    x = np.arange(len(names))
    w = 0.36

    fig, ax = plt.subplots(figsize=figsize)
    b1 = ax.bar(x - w/2, day1, width=w, color=BURGUNDY, label=D.AIRLINE_DAY1_LABEL)
    b2 = ax.bar(x + w/2, day2, width=w, color=ACCENT, label=D.AIRLINE_DAY2_LABEL)
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


def cargo_chart(mode, figsize=(3.3, 2.2)):
    c = D.CARGO
    fig, ax = plt.subplots(figsize=figsize)

    if mode == "Split":
        labels = ["Export", "Import", "Outbound", "Inbound"]
        values = [c["export"], c["import"], c["outbound"], c["inbound"]]
        # colour family signals the group: accent (red) = International,
        # burgundy = Domestic — same language as the Pax/Flights split chart.
        colors = [ACCENT, ACCENT_LIGHT, BURGUNDY, BURGUNDY_LIGHT]
        x = np.arange(4)
        bars = ax.bar(x, values, width=0.6, color=colors, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=6.4)

        ymax = max(values) * 1.42
        ax.set_ylim(0, ymax)

        # shaded bands + a divider so the Export/Import vs Outbound/Inbound
        # grouping is visible even before reading the labels
        ax.axvspan(-0.5, 1.5, color=ACCENT_LIGHT, alpha=0.15, zorder=0)
        ax.axvspan(1.5, 3.5, color=BURGUNDY_LIGHT, alpha=0.15, zorder=0)
        ax.axvline(1.5, color="#ccc", linewidth=0.8, zorder=1)

        # explicit group headers above each pair of bars
        ax.text(0.5, ymax * 0.94, "INTERNATIONAL", ha="center", va="top",
                fontsize=6.3, fontweight="bold", color=ACCENT)
        ax.text(2.5, ymax * 0.94, "DOMESTIC", ha="center", va="top",
                fontsize=6.3, fontweight="bold", color=BURGUNDY)
    else:
        intl_total = c["export"] + c["import"]
        dom_total = c["outbound"] + c["inbound"]
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
