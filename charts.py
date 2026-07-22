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
    
    names_r = names[::-1]
    dom_r = dom[::-1]
    intl_r = intl[::-1]

    fig = go.Figure()

    if mode == "Split":
        fig.add_trace(go.Bar(
            y=names_r, x=dom_r, name="Domestic", orientation="h",
            marker_color=BURGUNDY,
            text=[f"{v:,}" for v in dom_r], textposition="outside",
            textfont=dict(size=8.5, color=TEXT), cliponaxis=False,
            hovertemplate="%{y}<br>Domestic: %{x:,}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            y=names_r, x=intl_r, name="International", orientation="h",
            marker_color=ACCENT,
            text=[f"{v:,}" for v in intl_r], textposition="outside",
            textfont=dict(size=8.5, color=TEXT), cliponaxis=False,
            hovertemplate="%{y}<br>International: %{x:,}<extra></extra>",
        ))
        barmode = "group"
        max_val = max(dom_r + intl_r) if (dom_r + intl_r) else 1
    else:
        total_r = [d + i for d, i in zip(dom_r, intl_r)]
        fig.add_trace(go.Bar(
            y=names_r, x=total_r, orientation="h",
            marker_color=BURGUNDY, showlegend=False,
            text=[f"{v:,}" for v in total_r], textposition="outside",
            textfont=dict(size=8.5, color=TEXT), cliponaxis=False,
            hovertemplate="%{y}<br>Total: %{x:,}<extra></extra>",
        ))
        barmode = "group"
        max_val = max(total_r) if total_r else 1

    fig.update_layout(
        barmode=barmode,
        margin=dict(l=4, r=55, t=4, b=4),
        height=320,  # Reduced from 390 to prevent vertical overflow
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
                      tickfont=dict(size=9), rangemode="tozero",
                      range=[0, max_val * 1.22])
    fig.update_yaxes(title=None, tickfont=dict(size=9), automargin=True)
    return fig
