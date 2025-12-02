import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
from PIL import Image
import base64

# ----- BASIC CONFIG -----
st.set_page_config(
    page_title="DataDriven Bookkeeping Demo",
    layout="centered",
)

# ----- COLORS -----
PRIMARY_GREEN = "#053126"
OFF_WHITE = "#F6F5F0"
GOLD = "#F4C542"

# ----- GLOBAL CSS -----
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {PRIMARY_GREEN};
        color: {OFF_WHITE};
    }}
    section.main > div {{
        background-color: {PRIMARY_GREEN};
    }}
    h1, h2, h3, h4, h5, h6, label {{
        color: {OFF_WHITE};
    }}
    p, li, span, div {{
        color: {OFF_WHITE};
    }}
    a {{
        color: {GOLD};
        font-weight:600;
    }}
    a:hover {{
        color: #FFE27A;
    }}
    div[data-testid="stMetricValue"] {{
        color: {OFF_WHITE};
    }}
    div[data-testid="stMetricDelta"] {{
        color: {GOLD};
    }}
    div[data-testid="stDataFrame"] {{
        background-color:#ffffff !important;
        color:#000000 !important;
        border-radius:6px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----- SMALL LOGO TOP-LEFT -----
logo_bytes = open("data/logo_withTagline.png", "rb").read()
logo_b64 = base64.b64encode(logo_bytes).decode()

st.markdown(
    f"""
    <div style="
        position:fixed;
        top:10px;
        left:10px;
        z-index:999;
    ">
        <img src="data:image/png;base64,{logo_b64}"
             style="width:90px; border-radius:4px;">
    </div>
    """,
    unsafe_allow_html=True,
)

# ----- DATA DIRECTORY -----
DATA_DIR = Path("data")

# ---------- INDUSTRY LABEL UPDATE ----------
CONSTR_LABEL = "Construction/Plumbing/Electrical Company"

# ---------- FILE MAPPINGS ----------
INDUSTRY_FILES = {
    CONSTR_LABEL: "pl_construction.csv",
    "Dental Practice": "pl_dental.csv",
    "Medical Office / Clinic": "pl_medical_office.csv",
    "Lawn Care & Landscaping": "pl_lawn_care.csv",
    "Kitchen / Home Contractor": "pl_kitchen_contractor.csv",
    "Restaurant": "pl_restaurant.csv",
    "Long-Haul Trucking": "pl_trucking_longhaul.csv",
}

INDUSTRY_TREND_FILES = {
    CONSTR_LABEL: "pl_construction_monthly_trend.csv",
    "Dental Practice": "pl_dental_monthly_trend.csv",
    "Medical Office / Clinic": "pl_medical_office_monthly_trend.csv",
    "Lawn Care & Landscaping": "pl_lawn_care_monthly_trend.csv",
    "Kitchen / Home Contractor": "pl_kitchen_contractor_monthly_trend.csv",
    "Restaurant": "pl_restaurant_monthly_trend.csv",
    "Long-Haul Trucking": "pl_trucking_longhaul_monthly_trend.csv",
}

INDUSTRY_BS_FILES = {
    CONSTR_LABEL: "bs_construction.csv",
    "Dental Practice": "bs_dental.csv",
    "Medical Office / Clinic": "bs_medical_office.csv",
    "Lawn Care & Landscaping": "bs_lawn_care.csv",
    "Kitchen / Home Contractor": "bs_kitchen_contractor.csv",
    "Restaurant": "bs_restaurant.csv",
    "Long-Haul Trucking": "bs_trucking_longhaul.csv",
}

INDUSTRY_CF_FILES = {
    CONSTR_LABEL: "cf_construction.csv",
    "Dental Practice": "cf_dental.csv",
    "Medical Office / Clinic": "cf_medical_office.csv",
    "Lawn Care & Landscaping": "cf_lawn_care.csv",
    "Kitchen / Home Contractor": "cf_kitchen_contractor.csv",
    "Restaurant": "cf_restaurant.csv",
    "Long-Haul Trucking": "cf_trucking_longhaul.csv",
}

INDUSTRY_SPATIAL_FILES = {
    CONSTR_LABEL: "spatial_construction.csv",
    "Dental Practice": "spatial_dentist.csv",
    "Medical Office / Clinic": "spatial_medical_office.csv",
    "Lawn Care & Landscaping": "spatial_lawn_care.csv",
    "Kitchen / Home Contractor": "spatial_kitchen_contractor.csv",
    "Restaurant": "spatial_restaurant.csv",
    "Long-Haul Trucking": "spatial_trucking_longhaul.csv",
}

# ----- HELPERS -----

def render_kpis(kpis, cols_per_row=2):
    for i in range(0, len(kpis), cols_per_row):
        row = kpis[i:i + cols_per_row]
        cols = st.columns(len(row))
        for col, (label, value, delta) in zip(cols, row):
            col.metric(label, value, delta)

@st.cache_data
def load_pl_data(filename):
    df = pd.read_csv(DATA_DIR / filename)
    for col in ["Current Period", "Prior Period", "Change"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@st.cache_data
def load_csv(filename):
    return pd.read_csv(DATA_DIR / filename)

def split_sections(df):
    return (
        df[df["Section"] == "REVENUES"].copy(),
        df[df["Section"] == "COST OF GOODS SOLD"].copy(),
        df[df["Section"] == "OPERATING EXPENSES"].copy(),
        df[df["Section"] == "SUMMARY"].set_index("Line Item")
    )

def get_summary_value(summary, name):
    return float(summary.loc[name, "Current Period"]) if name in summary.index else 0.0

# ----- PAGE CONTROLS -----
st.markdown("<br><br>", unsafe_allow_html=True)  # spacing under logo

colA, colB = st.columns([1,1])
with colA:
    industry = st.selectbox("Business Type", list(INDUSTRY_FILES.keys()))

with colB:
    page = st.radio(
        "View",
        ["Profit & Loss", "Insights", "Spatial", "Trends", "Balance Sheet", "Cash Flow"],
        horizontal=True
    )

st.markdown("---")

# ----- LOAD DATA -----
filename = INDUSTRY_FILES[industry]
df = load_pl_data(filename)
revenues, cogs, opex, summary = split_sections(df)

total_rev_cur = revenues[revenues["Line Item"].str.contains("TOTAL", case=False)]["Current Period"].sum()
total_rev_prev = revenues[revenues["Line Item"].str.contains("TOTAL", case=False)]["Prior Period"].sum()

gross_profit = get_summary_value(summary, "GROSS PROFIT (LOSS)")
operating_profit = get_summary_value(summary, "OPERATING PROFIT (LOSS)")
net_income = get_summary_value(summary, "NET INCOME (LOSS)")

gross_margin = gross_profit / total_rev_cur if total_rev_cur else 0
oper_margin = operating_profit / total_rev_cur if total_rev_cur else 0
net_margin = net_income / total_rev_cur if total_rev_cur else 0

# =========================================================
#                     MAIN PAGES
# =========================================================

if page == "Profit & Loss":
    st.subheader(f"Profit & Loss – {industry}")

    kpis = [
        ("Total Revenue", f"${total_rev_cur:,.0f}", f"${total_rev_cur-total_rev_prev:,.0f}"),
        ("Gross Profit", f"${gross_profit:,.0f}", f"{gross_margin*100:,.1f}%"),
        ("Operating Profit", f"${operating_profit:,.0f}", f"{oper_margin*100:,.1f}%"),
        ("Net Income", f"${net_income:,.0f}", f"{net_margin*100:,.1f}%"),
    ]
    render_kpis(kpis)

    st.markdown("---")

    # Revenue vs COGS chart
    rev_cogs_df = pd.DataFrame({
        "Category": ["Revenue", "COGS"],
        "Current": [total_rev_cur, cogs["Current Period"].sum()],
        "Prior": [total_rev_prev, cogs["Prior Period"].sum()]
    })

    fig = px.bar(
        rev_cogs_df.melt(id_vars="Category", var_name="Period", value_name="Amount"),
        x="Category", y="Amount", color="Period",
        barmode="group", title="Revenue vs COGS"
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Full P&L"):
        st.dataframe(df, use_container_width=True)

# ---------------- Insights -----------------

elif page == "Insights":
    st.subheader(f"Commentary & Insights – {industry}")

    delta = net_income - summary.loc["NET INCOME (LOSS)", "Prior Period"] \
        if "NET INCOME (LOSS)" in summary.index else 0

    st.write(f"- Current Revenue: **${total_rev_cur:,.0f}**")
    st.write(f"- Net Income: **${net_income:,.0f}**")
    st.write(f"- Change: **${delta:,.0f}**")

# ---------------- Spatial -----------------

elif page == "Spatial":
    st.subheader(f"Where Your Clients Are – {industry}")

    sdf = load_csv(INDUSTRY_SPATIAL_FILES[industry])

    # Basic requirements
    for col in ["Latitude", "Longitude"]:
        sdf[col] = pd.to_numeric(sdf[col], errors="coerce")

    sdf_clean = sdf.dropna(subset=["Latitude", "Longitude"])

    fig_map = px.scatter_mapbox(
        sdf_clean,
        lat="Latitude", lon="Longitude",
        size=sdf_clean.get("Revenue_Current", None),
        color=sdf_clean.get("Revenue_Current", None),
        zoom=8,
        mapbox_style="open-street-map",
        hover_name="Zip"
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ---------------- Trends -----------------

elif page == "Trends":
    st.subheader(f"Monthly Trends – {industry}")

    tdf = load_csv(INDUSTRY_TREND_FILES[industry])

    fig = px.line(
        tdf,
        x="Month", y=["Total_Revenue", "Net_Income"],
        markers=True, title="Revenue & Net Income Trend"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Balance Sheet -----------------

elif page == "Balance Sheet":
    st.subheader(f"Balance Sheet – {industry}")
    bs = load_csv(INDUSTRY_BS_FILES[industry])
    st.dataframe(bs, use_container_width=True)

# ---------------- Cash Flow -----------------

elif page == "Cash Flow":
    st.subheader(f"Cash Flow – {industry}")
    cf = load_csv(INDUSTRY_CF_FILES[industry])
    st.dataframe(cf, use_container_width=True)

# =========================================================
#                         FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    f"""
    <div style='text-align:center; color:{OFF_WHITE}; font-size:15px; margin-top:15px; line-height:1.4;'>
        This sample report was created for small business owners by <b>Dr. Ahmed Askar</b>
        to give you a clear financial picture.<br><br>

        <a href="https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ0RlDh3HxjIPN_w5wEiSXf3IQ29bGR2K1F0NiZ8YzWy7MgbJmRHWpDbaKgiGCJdHPToLw7YVR_y"
           target="_blank"
           style="color:{GOLD}; font-size:16px; text-decoration:none; font-weight:700;">
           📅 Book a Free Consultation
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
