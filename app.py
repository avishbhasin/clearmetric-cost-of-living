"""
Cost of Living Comparator — Free Web Tool by ClearMetric
https://clearmetric.gumroad.com

Product T10. Helps remote workers and movers compare cost of living between cities.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from data import (
    CITY_DATA,
    CITIES,
    CATEGORIES,
    RADAR_CATEGORIES,
    LIFESTYLE_MULTIPLIERS,
    HOUSEHOLD_MULTIPLIERS,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Cost of Living Comparator — ClearMetric",
    page_icon="🌆",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS (navy theme)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    .stMetric { background: #f8f9fa; border-radius: 8px; padding: 12px; border-left: 4px solid #1a365d; }
    h1 { color: #1a365d; }
    h2, h3 { color: #2C3E50; }
    .verdict-box {
        background: linear-gradient(135deg, #1a365d 0%, #2C3E50 100%);
        color: white; padding: 20px; border-radius: 12px; text-align: center;
        margin: 20px 0; font-size: 1.1rem;
    }
    .cta-box {
        background: linear-gradient(135deg, #1a365d 0%, #2C3E50 100%);
        color: white; padding: 24px; border-radius: 12px; text-align: center;
        margin: 20px 0;
    }
    .cta-box a { color: #D5D8DC; text-decoration: none; font-weight: bold; font-size: 1.1rem; }
    div[data-testid="stSidebar"] { background: #f8f9fa; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# 🌆 Cost of Living Comparator")
st.markdown("**Compare cost of living between cities.** Find your equivalent salary and see monthly budget differences.")
st.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar — User inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## Your Details")

    current_city = st.selectbox(
        "Current City",
        CITIES,
        index=CITIES.index("New York") if "New York" in CITIES else 0,
    )
    target_city = st.selectbox(
        "Target City",
        CITIES,
        index=CITIES.index("Austin") if "Austin" in CITIES else 10,
    )

    if current_city == target_city:
        st.warning("Pick different cities to compare.")

    st.markdown("### Income & Household")
    annual_salary = st.number_input(
        "Current Annual Salary ($)",
        value=100_000,
        min_value=1_000,
        max_value=2_000_000,
        step=5_000,
        format="%d",
    )
    household_size = st.number_input(
        "Household Size",
        value=2,
        min_value=1,
        max_value=6,
        step=1,
        format="%d",
    )
    lifestyle = st.selectbox(
        "Lifestyle",
        list(LIFESTYLE_MULTIPLIERS.keys()),
        index=1,
    )
    housing_type = st.radio(
        "Renter or Homeowner",
        ["Renter", "Homeowner"],
        index=0,
    )

# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------
curr = CITY_DATA[current_city]
targ = CITY_DATA[target_city]

# Equivalent salary in target city
equiv_salary = annual_salary * (targ["overall"] / curr["overall"]) if curr["overall"] else 0
salary_diff = equiv_salary - annual_salary

# Category-by-category comparison
cat_comparison = {
    c: {
        "current": curr[c],
        "target": targ[c],
        "diff_pct": ((targ[c] - curr[c]) / curr[c] * 100) if curr[c] else 0,
    }
    for c in CATEGORIES
}

# Monthly budget estimate (lifestyle × salary / 12, adjusted by household)
lifestyle_mult = LIFESTYLE_MULTIPLIERS[lifestyle]
household_mult = HOUSEHOLD_MULTIPLIERS.get(household_size, 2.0)

# Base monthly budget at current salary (single person equivalent)
base_monthly_current = annual_salary / 12 * lifestyle_mult
base_monthly_target_equiv = equiv_salary / 12 * lifestyle_mult

# Adjust for household (rough: larger household = higher total but lower per-person)
monthly_budget_current = base_monthly_current * (household_mult / 2.0)  # normalize to 2-person
monthly_budget_target = base_monthly_target_equiv * (household_mult / 2.0)

# Annual savings comparison (difference in cost to maintain same lifestyle)
annual_savings_change = (annual_salary - equiv_salary)  # positive = target cheaper

# ---------------------------------------------------------------------------
# Display — Key metrics
# ---------------------------------------------------------------------------
st.markdown("## Key Results")

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Equivalent Salary in Target",
    f"${equiv_salary:,.0f}",
    help=f"Salary needed in {target_city} for same purchasing power",
)
m2.metric(
    "Monthly Difference",
    f"${(monthly_budget_target - monthly_budget_current):+,.0f}",
    help="Change in monthly budget to maintain lifestyle",
)
m3.metric(
    "Annual Savings Change",
    f"${annual_savings_change:+,.0f}",
    help="Positive = target city cheaper; negative = more expensive",
)
m4.metric(
    "Overall Index",
    f"{curr['overall']} → {targ['overall']}",
    help="NYC = 100. Lower = cheaper.",
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
if salary_diff > 0:
    verdict = f"You'd need **${salary_diff:,.0f} more** per year in {target_city} to maintain your lifestyle."
    verdict_class = "verdict-box"
else:
    verdict = f"You'd need **${abs(salary_diff):,.0f} less** per year in {target_city} — your money goes further there."
    verdict_class = "verdict-box"

st.markdown(f'<div class="{verdict_class}">{verdict}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Radar chart — Category comparison (6 categories)
# ---------------------------------------------------------------------------
st.markdown("## Category Comparison (Radar)")

radar_cats = [c.replace("_", " ").title() for c in RADAR_CATEGORIES]
fig_radar = go.Figure()
fig_radar.add_trace(
    go.Scatterpolar(
        r=[curr[c] for c in RADAR_CATEGORIES],
        theta=radar_cats,
        fill="toself",
        name=current_city,
        line_color="#1a365d",
    )
)
fig_radar.add_trace(
    go.Scatterpolar(
        r=[targ[c] for c in RADAR_CATEGORIES],
        theta=radar_cats,
        fill="toself",
        name=target_city,
        line_color="#0097A7",
    )
)
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, max(max(curr[c], targ[c]) for c in RADAR_CATEGORIES) * 1.1])),
    showlegend=True,
    legend=dict(orientation="h", y=1.02),
    height=450,
    margin=dict(t=40, b=40),
)
st.plotly_chart(fig_radar, use_container_width=True)

# ---------------------------------------------------------------------------
# Horizontal bar — Category index comparison
# ---------------------------------------------------------------------------
st.markdown("## Category Index Comparison (NYC = 100)")

df_cat = pd.DataFrame({
    "Category": radar_cats,
    current_city: [curr[c] for c in CATEGORIES],
    target_city: [targ[c] for c in CATEGORIES],
})

fig_bar = go.Figure()
fig_bar.add_trace(
    go.Bar(
        name=current_city,
        y=df_cat["Category"],
        x=df_cat[current_city],
        orientation="h",
        marker_color="#1a365d",
    )
)
fig_bar.add_trace(
    go.Bar(
        name=target_city,
        y=df_cat["Category"],
        x=df_cat[target_city],
        orientation="h",
        marker_color="#0097A7",
    )
)
fig_bar.update_layout(
    barmode="group",
    height=350,
    xaxis_title="Index (NYC = 100)",
    margin=dict(t=40, b=40),
    legend=dict(orientation="h", y=1.02),
)
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------------------
# Monthly budget side-by-side
# ---------------------------------------------------------------------------
st.markdown("## Monthly Budget Estimate")

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"### {current_city}")
    st.metric("Estimated Monthly Budget", f"${monthly_budget_current:,.0f}")
    st.caption(f"Based on {lifestyle} lifestyle, household of {household_size}")
    st.markdown(f"**Housing (median rent):** 1BR ${curr['rent_1br']:,} / 2BR ${curr['rent_2br']:,}")

with col2:
    st.markdown(f"### {target_city}")
    st.metric("Estimated Monthly Budget", f"${monthly_budget_target:,.0f}")
    st.caption(f"Based on {lifestyle} lifestyle, household of {household_size}")
    st.markdown(f"**Housing (median rent):** 1BR ${targ['rent_1br']:,} / 2BR ${targ['rent_2br']:,}")

# ---------------------------------------------------------------------------
# CTA — Paid Excel
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div class="cta-box">
    <h3 style="color: white; margin: 0 0 8px 0;">Want the Full Excel Spreadsheet?</h3>
    <p style="margin: 0 0 16px 0;">
        Get the <strong>ClearMetric Cost of Living Comparator</strong> — $9.99<br>
        ✓ City Comparator — pick 2 cities, see equivalent salary + category breakdown<br>
        ✓ Multi-City Ranking — all 30 cities ranked by index<br>
        ✓ How To Use guide<br>
    </p>
    <a href="https://clearmetric.gumroad.com/l/cost-of-living" target="_blank">
        Get It on Gumroad — $9.99 →
    </a>
</div>
""", unsafe_allow_html=True)

# Cross-sell
st.markdown("### More from ClearMetric")
cx1, cx2, cx3 = st.columns(3)
with cx1:
    st.markdown("""
    **🏠 Rent vs Buy** — $12.99
    Break-even analysis, 30-year comparison.
    [Get it →](https://clearmetric.gumroad.com/l/rent-vs-buy)
    """)
with cx2:
    st.markdown("""
    **📊 Budget Planner** — $13.99
    Track income, expenses, savings with 50/30/20.
    [Get it →](https://clearmetric.gumroad.com/l/budget-planner)
    """)
with cx3:
    st.markdown("""
    **🚗 Car Affordability** — $9.99
    20/4/10 rule, total cost of ownership.
    [Get it →](https://clearmetric.gumroad.com/l/car-affordability)
    """)

# Footer
st.markdown("---")
st.caption(
    "© 2026 ClearMetric | [clearmetric.gumroad.com](https://clearmetric.gumroad.com) | "
    "This tool is for educational purposes only. Not financial advice."
)
