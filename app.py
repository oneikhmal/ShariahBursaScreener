"""
app.py — Bursa Shariah Screener
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import time
import sys
import os
import textwrap

sys.path.insert(0, os.path.dirname(__file__))
from scraper import scrape_all, BURSA_TICKERS
from screener import run_screening, summary_stats, VERDICT_HALAL, VERDICT_PURIFY, VERDICT_FAIL, VERDICT_NODATA

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bursa Shariah Screener",
    page_icon="☪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
    background-color: #080c14 !important;
    color: #d4dde9 !important;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 1400px; }

/* ── METRIC CARDS ── */
.metric-card {
    background: #0d1520;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.metric-card.halal::before  { background: #10b981; }
.metric-card.purify::before { background: #f59e0b; }
.metric-card.fail::before   { background: #ef4444; }
.metric-card.total::before  { background: #5b8fff; }

.metric-value {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-value.green  { color: #10b981; }
.metric-value.amber  { color: #f59e0b; }
.metric-value.red    { color: #ef4444; }
.metric-value.blue   { color: #5b8fff; }
.metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4a5568;
}

/* ── VERDICT BADGES ── */
.badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    padding: 0.25rem 0.65rem;
    border-radius: 3px;
}
.badge-halal  { background: rgba(16,185,129,0.12); color: #10b981; border: 1px solid rgba(16,185,129,0.25); }
.badge-purify { background: rgba(245,158,11,0.12);  color: #f59e0b; border: 1px solid rgba(245,158,11,0.25); }
.badge-fail   { background: rgba(239,68,68,0.10);   color: #ef4444; border: 1px solid rgba(239,68,68,0.25); }
.badge-nodata { background: rgba(107,114,128,0.1);  color: #6b7280; border: 1px solid rgba(107,114,128,0.2); }

/* ── HEADER ── */
.app-header {
    display: flex;
    align-items: baseline;
    gap: 1.2rem;
    margin-bottom: 0.25rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.app-title {
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #e8edf4;
}
.app-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #3d5166;
    letter-spacing: 0.1em;
}

/* ── RATIO BARS ── */
.ratio-bar-wrap {
    background: rgba(255,255,255,0.05);
    border-radius: 2px;
    height: 5px;
    width: 100%;
    overflow: hidden;
    margin-top: 3px;
}
.ratio-bar {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #0a0f1a !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }

/* ── STOCK DETAIL ── */
.detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 0.85rem;
}
.detail-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #4a5568;
    letter-spacing: 0.08em;
}
.detail-value { color: #d4dde9; font-weight: 600; }

/* ── DATAFRAME ── */
.stDataFrame { background: #0d1520 !important; }
iframe { background: #0d1520 !important; }

/* ── SECTION LABEL ── */
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: #3d5166;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    margin-top: 2rem;
}

/* ── CRITERIA ROW ── */
.criteria-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.7rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 0.83rem;
}
.criteria-icon { font-size: 1rem; width: 1.4rem; text-align: center; }
.criteria-name { flex: 1; color: #8a9ab5; }
.criteria-value { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)


# ── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    """Fetch + screen all stocks. Cached for 1 hour."""
    raw = scrape_all(delay=0.4)
    results = run_screening(raw)
    return results


# ── HELPERS ──────────────────────────────────────────────────────────────────
def fmt_myr(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    if val >= 1e9:
        return f"MYR {val/1e9:.2f}B"
    if val >= 1e6:
        return f"MYR {val/1e6:.1f}M"
    return f"MYR {val:,.0f}"

def fmt_pct(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    return f"{val:.1%}"

def verdict_badge(verdict):
    cls_map = {
        VERDICT_HALAL:  "badge-halal",
        VERDICT_PURIFY: "badge-purify",
        VERDICT_FAIL:   "badge-fail",
        VERDICT_NODATA: "badge-nodata",
    }
    labels = {
        VERDICT_HALAL:  "✓ HALAL",
        VERDICT_PURIFY: "◐ PURIFY",
        VERDICT_FAIL:   "✗ NOT COMPLIANT",
        VERDICT_NODATA: "? NO DATA",
    }
    cls = cls_map.get(verdict, "badge-nodata")
    label = labels.get(verdict, verdict)
    return f'<span class="badge {cls}">{label}</span>'

def pass_icon(val):
    if val is True:  return "✅"
    if val is False: return "❌"
    return "⚠️"

def ratio_bar_html(ratio, threshold=0.33, color_pass="#10b981", color_fail="#ef4444"):
    if ratio is None or (isinstance(ratio, float) and np.isnan(ratio)):
        return ""
    pct = min((ratio / threshold), 1.0) * 100
    color = color_pass if ratio < threshold else color_fail
    return (f'<div style="background:rgba(255,255,255,0.06);border-radius:2px;height:5px;'
            f'width:100%;overflow:hidden;margin-bottom:0.25rem;">'
            f'<div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:2px;"></div></div>')


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div class="app-title">☪ Bursa Shariah Screener</div>
  <div class="app-subtitle">AAOIFI · KLSE · Live via Yahoo Finance</div>
</div>
""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")

    verdict_filter = st.multiselect(
        "Verdict",
        options=[VERDICT_HALAL, VERDICT_PURIFY, VERDICT_FAIL, VERDICT_NODATA],
        default=[VERDICT_HALAL, VERDICT_PURIFY],
        format_func=lambda v: {
            VERDICT_HALAL: "✓ Halal",
            VERDICT_PURIFY: "◐ Purify",
            VERDICT_FAIL: "✗ Not Compliant",
            VERDICT_NODATA: "? No Data",
        }[v]
    )

    sector_options = ["All Sectors"]
    search_query = st.text_input("Search company name", placeholder="e.g. Nestle, Tenaga...")

    st.markdown("---")
    st.markdown("### ⚙️ Screening Criteria")
    st.markdown("""
<div style="font-size:0.78rem; color:#4a5568; line-height:1.9; font-family:'JetBrains Mono',monospace;">
<b style="color:#8a9ab5">1. Business Activity</b><br>
Excludes: banking, insurance, gambling, alcohol, tobacco, defense<br><br>
<b style="color:#8a9ab5">2. Debt Ratio</b><br>
Total Debt / Market Cap &lt; 33%<br><br>
<b style="color:#8a9ab5">3. Cash Ratio</b><br>
(Cash + Receivables) / Market Cap &lt; 33%<br><br>
<b style="color:#8a9ab5">4. Interest Revenue</b><br>
Interest Income / Total Revenue:<br>
• &lt; 5%  → Halal ✓<br>
• 5–33% → Purify ◐ (donate %)<br>
• &gt; 33% → Not Compliant ✗
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    refresh = st.button("🔄 Refresh Data", use_container_width=True)
    if refresh:
        st.cache_data.clear()
        st.rerun()

    st.markdown("""
<div style="font-size:0.65rem; color:#3d5166; font-family:'JetBrains Mono',monospace; margin-top:1rem;">
Data: Yahoo Finance · Cached 1hr<br>
Methodology: AAOIFI FAS<br>
Not financial advice.
</div>
""", unsafe_allow_html=True)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
with st.spinner("Fetching Bursa data via Yahoo Finance…"):
    df = load_data()

stats = summary_stats(df)

# ── KPI ROW ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card total">
      <div class="metric-value blue">{stats['total']}</div>
      <div class="metric-label">Stocks Screened</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card halal">
      <div class="metric-value green">{stats['halal']} <span style="font-size:1.1rem;color:#047857">({stats['halal_pct']}%)</span></div>
      <div class="metric-label">Shariah Compliant</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card purify">
      <div class="metric-value amber">{stats['purify']}</div>
      <div class="metric-label">Requires Purification</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card fail">
      <div class="metric-value red">{stats['fail']}</div>
      <div class="metric-label">Not Compliant</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── CHARTS ROW ────────────────────────────────────────────────────────────────
ch1, ch2 = st.columns([1, 2])

with ch1:
    st.markdown('<div class="section-label">Verdict Breakdown</div>', unsafe_allow_html=True)
    pie_data = {
        "Halal":            stats["halal"],
        "Purify":           stats["purify"],
        "Not Compliant":    stats["fail"],
        "Insufficient Data":stats["nodata"],
    }
    fig_pie = go.Figure(go.Pie(
        labels=list(pie_data.keys()),
        values=list(pie_data.values()),
        hole=0.65,
        marker_colors=["#10b981", "#f59e0b", "#ef4444", "#374151"],
        textfont=dict(family="JetBrains Mono", size=11),
        hovertemplate="<b>%{label}</b><br>%{value} stocks<br>%{percent}<extra></extra>",
    ))
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#8a9ab5",
        showlegend=True,
        legend=dict(font=dict(family="JetBrains Mono", size=10), bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        annotations=[dict(
            text=f"<b>{stats['halal_pct']}%</b><br><span style='font-size:10px'>compliant</span>",
            x=0.5, y=0.5, font_size=16, showarrow=False,
            font_color="#10b981", font_family="Syne",
        )]
    )
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

with ch2:
    st.markdown('<div class="section-label">Debt Ratio by Stock (threshold: 33%)</div>', unsafe_allow_html=True)
    df_chart = df[df["debt_ratio"].notna()].sort_values("debt_ratio", ascending=True).copy()
    df_chart["color"] = df_chart["debt_ratio"].apply(
        lambda x: "#10b981" if x < 0.33 else "#ef4444"
    )
    fig_bar = go.Figure(go.Bar(
        x=df_chart["name"],
        y=df_chart["debt_ratio"] * 100,
        marker_color=df_chart["color"].tolist(),
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>Debt Ratio: %{y:.1f}%<extra></extra>",
    ))
    fig_bar.add_hline(
        y=33, line_dash="dash",
        line_color="rgba(245,158,11,0.5)", line_width=1.5,
        annotation_text="33% threshold",
        annotation_font=dict(family="JetBrains Mono", size=10, color="#f59e0b"),
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#8a9ab5",
        xaxis=dict(tickfont=dict(family="JetBrains Mono", size=9), gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(
            title="Debt / Mkt Cap (%)",
            tickfont=dict(family="JetBrains Mono", size=9),
            gridcolor="rgba(255,255,255,0.04)",
            ticksuffix="%",
        ),
        margin=dict(t=10, b=60, l=50, r=10),
        height=260,
        bargap=0.3,
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})


# ── FILTER & TABLE ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Screened Stocks</div>', unsafe_allow_html=True)

df_filtered = df.copy()
if verdict_filter:
    df_filtered = df_filtered[df_filtered["verdict"].isin(verdict_filter)]
if search_query:
    df_filtered = df_filtered[df_filtered["name"].str.contains(search_query, case=False, na=False)]

# Build display table
display_cols = {
    "name": "Company",
    "sector": "Sector",
    "verdict": "Verdict",
    "debt_ratio": "Debt Ratio",
    "cash_ratio": "Cash Ratio",
    "interest_revenue_ratio": "Interest/Rev",
    "purification_pct": "Purify %",
    "market_cap": "Mkt Cap",
}

df_display = df_filtered[list(display_cols.keys())].rename(columns=display_cols).copy()
df_display["Debt Ratio"]    = df_display["Debt Ratio"].apply(fmt_pct)
df_display["Cash Ratio"]    = df_display["Cash Ratio"].apply(fmt_pct)
df_display["Interest/Rev"]  = df_display["Interest/Rev"].apply(fmt_pct)
df_display["Purify %"]      = df_display["Purify %"].apply(
    lambda x: f"{x:.2f}%" if x is not None and not np.isnan(x) else "—"
)
df_display["Mkt Cap"]       = df_display["Mkt Cap"].apply(fmt_myr)

def color_verdict(val):
    colors = {
        VERDICT_HALAL:  "color: #10b981; font-weight: 700;",
        VERDICT_PURIFY: "color: #f59e0b; font-weight: 700;",
        VERDICT_FAIL:   "color: #ef4444; font-weight: 700;",
        VERDICT_NODATA: "color: #6b7280;",
    }
    return colors.get(val, "")

styled = df_display.style.applymap(color_verdict, subset=["Verdict"])
st.dataframe(
    styled,
    use_container_width=True,
    height=min(60 + len(df_display) * 35, 500),
    hide_index=True,
)

st.markdown(f"""
<div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#3d5166; margin-top:0.5rem;">
  Showing {len(df_display)} of {len(df)} stocks · Click a row below for detailed breakdown
</div>
""", unsafe_allow_html=True)


# ── DETAIL PANEL ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Stock Detail & Screening Breakdown</div>', unsafe_allow_html=True)

company_names = df_filtered["name"].tolist()
if not company_names:
    st.info("No stocks match the current filter.")
else:
    selected_name = st.selectbox("Select a stock to inspect:", company_names, label_visibility="collapsed")
    row = df[df["name"] == selected_name].iloc[0]

    d1, d2, d3 = st.columns([1.2, 1.2, 1.4])

    # ── Shared inline style constants (hardcoded, no f-string nesting) ──────────
    CARD     = "background:#0d1520; border:1px solid rgba(255,255,255,0.07); border-radius:10px; padding:1.4rem;"
    ROW      = "display:flex; justify-content:space-between; align-items:center; padding:0.55rem 0; border-bottom:1px solid rgba(255,255,255,0.05);"
    ROW_NB   = "display:flex; justify-content:space-between; align-items:center; padding:0.55rem 0;"
    LABEL_S  = "font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#4a5568; letter-spacing:0.05em;"
    VAL_S    = "color:#d4dde9; font-weight:600; font-size:0.85rem;"
    CRIT_ROW    = "display:flex; align-items:center; gap:0.75rem; padding:0.65rem 0; border-bottom:1px solid rgba(255,255,255,0.05);"
    CRIT_ROW_NB = "display:flex; align-items:center; gap:0.75rem; padding:0.65rem 0;"
    SEC_HDR  = "font-family:'JetBrains Mono',monospace; font-size:0.65rem; letter-spacing:0.18em; color:#3d5166; text-transform:uppercase; margin-bottom:1rem;"
    MONO_S   = "font-family:'JetBrains Mono',monospace;"

    with d1:
        price_str = f"MYR {row['price']:.2f}" if row['price'] else '—'
        st.markdown(f"""
        <div style="{CARD}">
          <div style="font-size:1.1rem; font-weight:700; letter-spacing:-0.02em; margin-bottom:0.3rem; color:#e8edf4;">{row['name']}</div>
          <div style="{MONO_S} font-size:0.7rem; color:#4a5568; margin-bottom:1rem;">{row['ticker']} · {row['sector']}</div>
          {verdict_badge(row['verdict'])}
          <div style="{ROW} margin-top:1rem;">
            <span style="{LABEL_S}">Price</span>
            <span style="{VAL_S}">{price_str}</span>
          </div>
          <div style="{ROW}">
            <span style="{LABEL_S}">Market Cap</span>
            <span style="{VAL_S}">{fmt_myr(row['market_cap'])}</span>
          </div>
          <div style="{ROW}">
            <span style="{LABEL_S}">Industry</span>
            <span style="{VAL_S} font-size:0.78rem;">{row['industry']}</span>
          </div>
          <div style="{ROW_NB}">
            <span style="{LABEL_S}">Total Revenue</span>
            <span style="{VAL_S}">{fmt_myr(row['total_revenue'])}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with d2:
        debt_color  = '#10b981' if row['pass_debt']  else '#ef4444'
        cash_color  = '#10b981' if row['pass_cash']  else '#ef4444'
        int_ratio   = row['interest_revenue_ratio'] or 0
        int_color   = '#f59e0b' if int_ratio >= 0.05 else '#10b981'
        sect_color  = '#10b981' if row['pass_sector'] else '#ef4444'
        sect_label  = 'PASS' if row['pass_sector'] else 'EXCLUDED'

        def inline_bar(ratio, threshold=0.33, c_pass="#10b981", c_fail="#ef4444"):
            if ratio is None or np.isnan(ratio): return ""
            pct = min((ratio / threshold), 1.0) * 100
            color = c_pass if ratio < threshold else c_fail
            return f"""<div style="background:rgba(255,255,255,0.06); border-radius:2px; height:5px; width:100%; overflow:hidden; margin-bottom:0.25rem;">
              <div style="width:{pct:.0f}%; height:100%; background:{color}; border-radius:2px;"></div></div>"""

        st.markdown(f"""
        <div style="{CARD}">
          <div style="{SEC_HDR}">Ratio Analysis</div>

          <div style="{CRIT_ROW}">
            <span style="font-size:1rem; width:1.2rem;">{pass_icon(row['pass_debt'])}</span>
            <span style="flex:1; color:#8a9ab5; font-size:0.83rem;">Debt Ratio</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:{debt_color}; font-weight:600;">{fmt_pct(row['debt_ratio'])}</span>
          </div>
          {inline_bar(row['debt_ratio'])}

          <div style="{CRIT_ROW}">
            <span style="font-size:1rem; width:1.2rem;">{pass_icon(row['pass_cash'])}</span>
            <span style="flex:1; color:#8a9ab5; font-size:0.83rem;">Cash Ratio</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:{cash_color}; font-weight:600;">{fmt_pct(row['cash_ratio'])}</span>
          </div>
          {inline_bar(row['cash_ratio'])}

          <div style="{CRIT_ROW}">
            <span style="font-size:1rem; width:1.2rem;">{pass_icon(row['pass_interest'])}</span>
            <span style="flex:1; color:#8a9ab5; font-size:0.83rem;">Interest / Revenue</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:{int_color}; font-weight:600;">{fmt_pct(row['interest_revenue_ratio'])}</span>
          </div>
          {inline_bar(row['interest_revenue_ratio'])}

          <div style="{CRIT_ROW_NB}">
            <span style="font-size:1rem; width:1.2rem;">{pass_icon(row['pass_sector'])}</span>
            <span style="flex:1; color:#8a9ab5; font-size:0.83rem;">Business Activity</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:{sect_color}; font-weight:600;">{sect_label}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    import textwrap

    import streamlit.components.v1 as components

    with d3:
        fail_reasons = row.get("fail_reasons", [])
        if isinstance(fail_reasons, str):
            import ast
            try:
                fail_reasons = ast.literal_eval(fail_reasons)
            except:
                fail_reasons = []

        purify_pct = row.get("purification_pct")
        purify_str = ""
        if row["verdict"] == VERDICT_PURIFY and purify_pct and not np.isnan(float(purify_pct)):
            purify_str = f"""
            <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.2); border-radius:6px; padding:1rem; margin-bottom:1rem;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#f59e0b; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.5rem;">Purification Required</div>
            <div style="font-size:1.5rem; font-weight:800; color:#f59e0b;">{float(purify_pct):.2f}%</div>
            <div style="font-size:0.78rem; color:#78716c;">of dividend/income to donate</div>
            </div>
            """

        if fail_reasons:
            items = "".join(
                f'<div style="display:flex; gap:0.5rem; padding:0.4rem 0; border-bottom:1px solid rgba(239,68,68,0.1); font-size:0.78rem; color:#fca5a5;">'
                f'<span style="color:#ef4444;">✗</span><span>{r}</span></div>'
                for r in fail_reasons
            )
            fail_html = f"""
            <div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#3d5166; margin-bottom:0.5rem;">Failure Reasons</div>
            {items}
            </div>
            """
        elif row["verdict"] == VERDICT_HALAL:
            fail_html = """
            <div style="background:rgba(16,185,129,0.07); border:1px solid rgba(16,185,129,0.15); border-radius:6px; padding:1rem;">
            <div style="color:#10b981; font-weight:700;">✓ All criteria passed</div>
            </div>
            """
        elif row["verdict"] == VERDICT_NODATA:
            fail_html = """
            <div style="background:rgba(107,114,128,0.08); border:1px solid rgba(107,114,128,0.15); border-radius:6px; padding:1rem;">
            <div style="color:#9ca3af;">⚠ Insufficient Data</div>
            </div>
            """
        else:
            fail_html = ""

        html = f"""
        <div style="{CARD}">
            <div style="{SEC_HDR}">Verdict Detail</div>
            {purify_str}
            {fail_html}
        </div>
        """

        components.html(html, height=320, scrolling=False)

        #st.markdown(html_block, unsafe_allow_html=True)
# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem; padding-top:1.5rem; border-top:1px solid rgba(255,255,255,0.06);
     font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#3d5166;
     display:flex; justify-content:space-between;">
  <span>Bursa Shariah Screener · Built by Ikhmal · Not financial advice</span>
  <span>Methodology: AAOIFI Financial Accounting Standard</span>
</div>
""", unsafe_allow_html=True)
