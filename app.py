import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
from PIL import Image

# ----- BASIC CONFIG -----
st.set_page_config(
    page_title="DataDriven Bookkeeping Demo",
    layout="centered",
)

# ----- BRANDED THEME (GREEN BACKGROUND + GOLD/WHITE TEXT) -----
PRIMARY_GREEN = "#053126"
OFF_WHITE = "#F6F5F0"
GOLD = "#F4C542"

st.markdown(
    f"""
    <style>
    /* App background + base text */
    .stApp {{
        background-color: {PRIMARY_GREEN};
        color: {OFF_WHITE};
    }}

    /* Main content area */
    section.main > div {{
        background-color: {PRIMARY_GREEN};
    }}

    /* Headings & labels */
    h1, h2, h3, h4, h5, h6, label, .stRadio label, .stSelectbox label {{
        color: {OFF_WHITE};
    }}

    /* Paragraphs and list text */
    p, li, span, div {{
        color: {OFF_WHITE};
    }}

    /* Links */
    a {{
        color: {GOLD};
    }}
    a:hover {{
        color: #FFE27A;
    }}

    /* Metrics */
    div[data-testid="stMetricValue"] {{
        color: {OFF_WHITE};
    }}
    div[data-testid="stMetricDelta"] {{
        color: {GOLD};
    }}

    /* DataFrames: keep them readable (white background, dark text) */
    div[data-testid="stDataFrame"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 6px;
    }}

    /* Expander headers */
    details > summary {{
        color: {OFF_WHITE};
    }}

    /* Radio/Selectbox options text */
    div[role="radiogroup"] label, div[data-baseweb="select"] * {{
        color: {OFF_WHITE};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = Path("data")

# Map industries to core P&L files
INDUSTRY_FILES = {
    "Construction Company": "pl_construction.csv",
    "Dental Practice": "pl_dental.csv",
    "Medical Office / Clinic": "pl_medical_office.csv",
    "Lawn Care & Landscaping": "pl_lawn_care.csv",
    "Kitchen / Home Contractor": "pl_kitchen_contractor.csv",
    "Restaurant": "pl_restaurant.csv",
    "Long-Haul Trucking": "pl_trucking_longhaul.csv",
}

# Monthly trend P&L
INDUSTRY_TREND_FILES = {
    "Construction Company": "pl_construction_monthly_trend.csv",
    "Dental Practice": "pl_dental_monthly_trend.csv",
    "Medical Office / Clinic": "pl_medical_office_monthly_trend.csv",
    "Lawn Care & Landscaping": "pl_lawn_care_monthly_trend.csv",
    "Kitchen / Home Contractor": "pl_kitchen_contractor_monthly_trend.csv",
    "Restaurant": "pl_restaurant_monthly_trend.csv",
    "Long-Haul Trucking": "pl_trucking_longhaul_monthly_trend.csv",
}

# Balance Sheets
INDUSTRY_BS_FILES = {
    "Construction Company": "bs_construction.csv",
    "Dental Practice": "bs_dental.csv",
    "Medical Office / Clinic": "bs_medical_office.csv",
    "Lawn Care & Landscaping": "bs_lawn_care.csv",
    "Kitchen / Home Contractor": "bs_kitchen_contractor.csv",
    "Restaurant": "bs_restaurant.csv",
    "Long-Haul Trucking": "bs_trucking_longhaul.csv",
}

# Cash Flow Statements
INDUSTRY_CF_FILES = {
    "Construction Company": "cf_construction.csv",
    "Dental Practice": "cf_dental.csv",
    "Medical Office / Clinic": "cf_medical_office.csv",
    "Lawn Care & Landscaping": "cf_lawn_care.csv",
    "Kitchen / Home Contractor": "cf_kitchen_contractor.csv",
    "Restaurant": "cf_restaurant.csv",
    "Long-Haul Trucking": "cf_trucking_longhaul.csv",
}

# Spatial ZIP data
INDUSTRY_SPATIAL_FILES = {
    "Construction Company": "spatial_construction.csv",
    "Dental Practice": "spatial_dentist.csv",
    "Medical Office / Clinic": "spatial_medical_office.csv",
    "Lawn Care & Landscaping": "spatial_lawn_care.csv",
    "Kitchen / Home Contractor": "spatial_kitchen_contractor.csv",
    "Restaurant": "spatial_restaurant.csv",
    "Long-Haul Trucking": "spatial_trucking_longhaul.csv",
}

# ---------- HELPERS FOR MOBILE LAYOUT ----------

def render_kpis(kpis, cols_per_row: int = 2):
    """
    Render a list of KPI tuples (label, value, delta) in rows
    with a fixed number of columns per row.
    Example kpis: [("Label", "Value", "Delta or None"), ...]
    """
    for i in range(0, len(kpis), cols_per_row):
        row = kpis[i:i + cols_per_row]
        cols = st.columns(len(row))
        for col, (label, value, delta) in zip(cols, row):
            with col:
                st.metric(label, value, delta)

# ---------- LOADERS ----------

@st.cache_data
def load_pl_data(filename: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / filename)
    for col in ["Current Period", "Prior Period", "Change"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / filename)

# Split P&L into sections
def split_sections(df: pd.DataFrame):
    revenues = df[df["Section"] == "REVENUES"].copy()
    cogs = df[df["Section"] == "COST OF GOODS SOLD"].copy()
    opex = df[df["Section"] == "OPERATING EXPENSES"].copy()
    summary = df[df["Section"] == "SUMMARY"].set_index("Line Item")
    return revenues, cogs, opex, summary

def get_summary_value(summary: pd.DataFrame, name: str) -> float:
    if name in summary.index:
        return float(summary.loc[name, "Current Period"])
    return 0.0

def generate_spatial_commentary(industry: str, sdf: pd.DataFrame) -> str:
    """Create a short, white-glove narrative about hot/cold ZIPs."""
    if sdf.empty:
        return "No spatial data available for this sample."

    # Prefer Profit_Current if present, else fall back to Revenue_Current
    value_col = "Profit_Current" if "Profit_Current" in sdf.columns else "Revenue_Current"
    if value_col not in sdf.columns:
        return "Spatial data is available, but key value columns are missing for this sample."

    metric_series = pd.to_numeric(sdf[value_col], errors="coerce")

    # Drop NaNs
    valid = ~metric_series.isna()
    if not valid.any():
        return "Spatial data is loaded, but there are no valid numeric values to analyze."

    metric_series = metric_series[valid]
    sdf_valid = sdf.loc[valid].copy()

    q20 = metric_series.quantile(0.2)
    q80 = metric_series.quantile(0.8)

    hot = sdf_valid[metric_series >= q80]
    cold = sdf_valid[metric_series <= q20]

    def fmt_zip_block(df_slice: pd.DataFrame) -> str:
        rows = []
        for _, row in df_slice.head(4).iterrows():
            try:
                z = int(row["Zip"])
            except Exception:
                z = row["Zip"]
            rows.append(f"{z} ({row['City']})")
        return ", ".join(rows)

    hot_txt = fmt_zip_block(hot) if not hot.empty else ""
    cold_txt = fmt_zip_block(cold) if not cold.empty else ""

    pieces = []
    if hot_txt:
        pieces.append(
            f"- **Hot spots** for {industry.lower()} performance are clustering around **{hot_txt}**."
        )
    if cold_txt:
        pieces.append(
            f"- **Cold spots** (underperforming ZIPs) include **{cold_txt}**."
        )

    if not pieces:
        return "Performance looks fairly even across ZIP codes with no strong hot or cold pockets."

    return "\n".join(pieces)

# ---------- BRAND HEADER WITH LOGO + CTA ----------

logo = Image.open("/mnt/data/logo_withTagline.png")
st.image(logo, use_column_width=True)

st.markdown(
    """
    <div style="
        text-align:center;
        font-size:20px;
        color:#F4C542;
        margin-top:-5px;
        margin-bottom:20px;
        font-weight:600;">
        This sample report was created for small businesses like yours by <b>Dr. Ahmed Askar</b><br>
        to give you, the business owner, a clear financial picture and empower your growth.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="
        background-color:rgba(255,255,255,0.10);
        padding:18px;
        border-radius:10px;
        text-align:center;
        border:1px solid #F4C542;
        color:#F6F5F0;
        font-size:17px;
        line-height:1.45;">

        <b>Need a report like this for your own business?</b><br><br>

        Call us for a quick consultation — this brief, free <b>30-minute consultation</b> is designed to give you clarity.<br>
        We’ll walk through your bookkeeping setup, discuss any pain points
        (invoicing, expenses, reconciliation, or reporting), and map out how a
        <b>data-driven approach</b> can give you clean books and deeper financial visibility.<br><br>

        You’ll leave with a tailored recommendation and clear next steps — even if you decide not to move forward.

        <br><br>
        <a href="https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ0RlDh3HxjIPN_w5wEiSXf3IQ29bGR2K1F0NiZ8YzWy7MgbJmRHWpDbaKgiGCJdHPToLw7YVR_y"
           target="_blank"
           style="
               background-color:#F4C542;
               color:#053126;
               padding:10px 22px;
               border-radius:8px;
               text-decoration:none;
               font-weight:700;">
           📅 Book Your Free 30-Min Consultation
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ---------- TOP CONTROLS (ALWAYS VISIBLE) ----------

with st.container():
    col1, col2 = st.columns([1, 1])

    with col1:
        industry = st.selectbox(
            "Sample client type",
            list(INDUSTRY_FILES.keys()),
            key="industry_select",
        )

    with col2:
        page = st.radio(
            "View",
            ["Profit & Loss", "Insights", "Spatial", "Trends", "Balance Sheet", "Cash Flow"],
            horizontal=True,
            key="view_radio",
        )

st.markdown("---")

# ---------- SHARED PRE-CALCS ----------

filename = INDUSTRY_FILES[industry]
df = load_pl_data(filename)
revenues, cogs, opex, summary = split_sections(df)

total_rev_cur = revenues.loc[
    revenues["Line Item"].str.contains("TOTAL", case=False), "Current Period"
].sum()
total_rev_prev = revenues.loc[
    revenues["Line Item"].str.contains("TOTAL", case=False), "Prior Period"
].sum()

gross_profit = get_summary_value(summary, "GROSS PROFIT (LOSS)")
operating_profit = get_summary_value(summary, "OPERATING PROFIT (LOSS)")
net_income = get_summary_value(summary, "NET INCOME (LOSS)")

gross_margin = gross_profit / total_rev_cur if total_rev_cur else 0
oper_margin = operating_profit / total_rev_cur if total_rev_cur else 0
net_margin = net_income / total_rev_cur if total_rev_cur else 0

# ---------- P&L PAGE ----------

if page == "Profit & Loss":
    st.subheader(f"Profit & Loss – {industry}")
    st.caption(
        "Demo only – sample numbers to show how DataDriven Bookkeeping can present your financials."
    )

    # KPIs (2 per row for mobile)
    kpis_pl = [
        (
            "Total Revenue (Current)",
            f"${total_rev_cur:,.0f}",
            f"${total_rev_cur - total_rev_prev:,.0f}",
        ),
        (
            "Gross Profit",
            f"${gross_profit:,.0f}",
            f"{gross_margin*100:,.1f}% margin",
        ),
        (
            "Operating Profit",
            f"${operating_profit:,.0f}",
            f"{oper_margin*100:,.1f}% margin",
        ),
        (
            "Net Income",
            f"${net_income:,.0f}",
            f"{net_margin*100:,.1f}% margin",
        ),
    ]
    render_kpis(kpis_pl, cols_per_row=2)

    st.markdown("---")

    # Revenue vs COGS
    st.subheader("Revenue vs Cost of Goods Sold")
    cogs_total_cur = cogs["Current Period"].sum()
    cogs_total_prev = cogs["Prior Period"].sum()

    rev_cogs_df = pd.DataFrame({
        "Category": ["Revenue", "Cost of Goods Sold"],
        "Current Period": [total_rev_cur, cogs_total_cur],
        "Prior Period": [total_rev_prev, cogs_total_prev],
    })

    rev_cogs_long = rev_cogs_df.melt(
        id_vars="Category",
        var_name="Period",
        value_name="Amount"
    )

    fig_rev_cogs = px.bar(
        rev_cogs_long,
        x="Category",
        y="Amount",
        color="Period",
        barmode="group",
        title="Current vs Prior Period – Revenue & COGS"
    )
    fig_rev_cogs.update_layout(yaxis_title="Amount ($)", xaxis_title="")
    st.plotly_chart(fig_rev_cogs, use_container_width=True)

    # Revenue breakdown
    st.subheader("Revenue Breakdown")
    rev_detail = revenues[~revenues["Line Item"].str.contains("TOTAL", case=False)]
    rev_detail_long = rev_detail.melt(
        id_vars=["Line Item"],
        value_vars=["Current Period", "Prior Period"],
        var_name="Period",
        value_name="Amount"
    )
    fig_rev_detail = px.bar(
        rev_detail_long,
        x="Line Item",
        y="Amount",
        color="Period",
        barmode="group",
        title="Revenue by Line Item"
    )
    fig_rev_detail.update_layout(yaxis_title="Amount ($)", xaxis_title="")
    st.plotly_chart(fig_rev_detail, use_container_width=True)

    # Top Opex
    st.subheader("Top Operating Expenses")
    opex_sorted = opex.sort_values("Current Period", ascending=False)
    fig_opex = px.bar(
        opex_sorted.head(15),
        x="Line Item",
        y="Current Period",
        title="Top Operating Expense Categories (Current Period)"
    )
    fig_opex.update_layout(yaxis_title="Amount ($)", xaxis_title="")
    st.plotly_chart(fig_opex, use_container_width=True)

    with st.expander("Full P&L Detail"):
        st.dataframe(df, use_container_width=True, height=400)

# ---------- INSIGHTS PAGE ----------

elif page == "Insights":
    st.subheader(f"Commentary & Insights – {industry}")

    net_income_cur = get_summary_value(summary, "NET INCOME (LOSS)")
    net_income_prev = summary.loc["NET INCOME (LOSS)", "Prior Period"] if "NET INCOME (LOSS)" in summary.index else 0
    delta = net_income_cur - net_income_prev
    pct = (delta / net_income_prev * 100) if net_income_prev else None

    st.markdown("#### High-level trend")
    st.write(f"- Revenue: **${total_rev_cur:,.0f}** (prior: ${total_rev_prev:,.0f})")
    st.write(f"- Net income: **${net_income_cur:,.0f}** (prior: ${net_income_prev:,.0f})")

    if pct is not None:
        st.write(f"- Net income change: **${delta:,.0f} ({pct:,.1f}%)**")

    if pct is not None and pct > 0:
        st.success("Profitability improved vs prior period.")
    elif pct is not None and pct < 0:
        st.warning("Profitability declined vs prior period.")
    else:
        st.info("Profitability is roughly flat vs prior period.")

    st.markdown(
        """
        This is the type of monthly summary your clients would receive in plain English,
        highlighting movements in revenue, margins, and major expense categories.
        """
    )

# ---------- SPATIAL PAGE (OpenStreetMap + blue→red scale) ----------

elif page == "Spatial":
    st.subheader(f"Where Your Clients Are – {industry}")
    spatial_file = INDUSTRY_SPATIAL_FILES[industry]
    sdf = load_csv(spatial_file)

    # Required base columns
    required_cols = ["Zip", "City", "State", "Latitude", "Longitude"]
    missing = [c for c in required_cols if c not in sdf.columns]
    if missing:
        st.error(f"The spatial file for this industry is missing required columns: {', '.join(missing)}")
        st.stop()

    # Coerce numeric columns
    for col in [
        "New_Customers", "Visits",
        "Revenue_Current", "Revenue_Prior",
        "Profit_Current", "Profit_Prior",
        "Latitude", "Longitude"
    ]:
        if col in sdf.columns:
            sdf[col] = pd.to_numeric(sdf[col], errors="coerce")

    # Summary metrics (with safe fallbacks)
    total_new = int(sdf["New_Customers"].sum()) if "New_Customers" in sdf.columns else 0
    total_visits = int(sdf["Visits"].sum()) if "Visits" in sdf.columns else 0
    total_rev = float(sdf["Revenue_Current"].sum()) if "Revenue_Current" in sdf.columns else 0.0
    total_profit = float(sdf["Profit_Current"].sum()) if "Profit_Current" in sdf.columns else 0.0

    kpis_spatial = [
        ("New Customers (Period)", f"{total_new:,}", None),
        ("Total Visits / Jobs", f"{total_visits:,}", None),
        ("Revenue (Current Period)", f"${total_rev:,.0f}", None),
        ("Estimated Profit (Current)", f"${total_profit:,.0f}", None),
    ]
    render_kpis(kpis_spatial, cols_per_row=2)

    st.markdown("---")

    st.subheader("ZIP-Level Performance Map")

    # Choose metric for color/size
    value_col = "Profit_Current" if "Profit_Current" in sdf.columns else "Revenue_Current"
    size_col = "Revenue_Current" if "Revenue_Current" in sdf.columns else value_col

    if value_col not in sdf.columns:
        st.warning("Spatial data is present, but no Profit_Current or Revenue_Current field is available to map.")
    else:
        # Drop rows with missing coords or metric
        sdf_map = sdf.dropna(subset=["Latitude", "Longitude", value_col]).copy()

        # Center & zoom for nicer OSM view
        center_lat = sdf_map["Latitude"].mean()
        center_lon = sdf_map["Longitude"].mean()

        fig_map = px.scatter_mapbox(
            sdf_map,
            lat="Latitude",
            lon="Longitude",
            color=value_col,
            size=size_col,
            hover_name="Zip",
            hover_data=[
                c for c in [
                    "City", "New_Customers", "Visits",
                    "Revenue_Current", "Profit_Current"
                ] if c in sdf.columns
            ],
            color_continuous_scale=["blue", "lightgray", "red"],  # blue=cold, red=hot
            zoom=9,
            center={"lat": center_lat, "lon": center_lon},
            title="Hot & Cold ZIP Codes (OpenStreetMap background)"
        )

        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_colorbar_title="Performance"
        )

        st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("Narrative Summary")
    st.markdown(generate_spatial_commentary(industry, sdf))

    with st.expander("Underlying ZIP Table"):
        st.dataframe(sdf, use_container_width=True, height=400)

# ---------- TRENDS PAGE ----------

elif page == "Trends":
    st.subheader(f"Monthly Trends – {industry}")
    trend_file = INDUSTRY_TREND_FILES[industry]
    tdf = load_csv(trend_file)

    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    if "Month" in tdf.columns:
        tdf["Month"] = pd.Categorical(tdf["Month"], categories=month_order, ordered=True)
        tdf = tdf.sort_values("Month")

    st.markdown("#### Revenue & Net Income Over Time")
    fig_trend = px.line(
        tdf,
        x="Month",
        y=["Total_Revenue", "Net_Income"],
        markers=True,
        title="Monthly Revenue & Net Income"
    )
    fig_trend.update_layout(yaxis_title="Amount ($)", legend_title="")
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("#### Gross Profit vs Operating Expenses")
    fig_gp = px.line(
        tdf,
        x="Month",
        y=["Gross_Profit", "Operating_Expenses"],
        markers=True,
        title="Gross Profit vs Operating Expenses"
    )
    fig_gp.update_layout(yaxis_title="Amount ($)", legend_title="")
    st.plotly_chart(fig_gp, use_container_width=True)

    with st.expander("Raw Trend Data"):
        st.dataframe(tdf, use_container_width=True, height=400)

# ---------- BALANCE SHEET PAGE ----------

elif page == "Balance Sheet":
    st.subheader(f"Balance Sheet – {industry}")
    bs_file = INDUSTRY_BS_FILES[industry]
    bs = load_csv(bs_file)

    total_assets = bs.loc[bs["Line Item"] == "TOTAL ASSETS", "Current Period"].iloc[0]
    total_liab = bs.loc[bs["Line Item"] == "TOTAL LIABILITIES", "Current Period"].iloc[0]
    total_equity = bs.loc[bs["Line Item"] == "TOTAL EQUITY", "Current Period"].iloc[0]

    kpis_bs = [
        ("Total Assets", f"${total_assets:,.0f}", None),
        ("Total Liabilities", f"${total_liab:,.0f}", None),
        ("Total Equity", f"${total_equity:,.0f}", None),
    ]
    render_kpis(kpis_bs, cols_per_row=2)

    st.markdown("---")
    st.subheader("Balance Sheet Detail")
    st.dataframe(bs, use_container_width=True, height=400)

# ---------- CASH FLOW PAGE ----------

elif page == "Cash Flow":
    st.subheader(f"Cash Flow – {industry}")
    cf_file = INDUSTRY_CF_FILES[industry]
    cf = load_csv(cf_file)

    beg = cf.loc[cf["Line Item"] == "Beginning Cash", "Current Period"].iloc[0]
    end = cf.loc[cf["Line Item"] == "Ending Cash", "Current Period"].iloc[0]
    delta = end - beg

    kpis_cf = [
        ("Beginning Cash", f"${beg:,.0f}", None),
        ("Ending Cash", f"${end:,.0f}", f"${delta:,.0f}"),
        ("Net Cash Change", f"${delta:,.0f}", None),
    ]
    render_kpis(kpis_cf, cols_per_row=2)

    st.markdown("---")

    st.subheader("Cash Flow by Section")
    st.dataframe(cf, use_container_width=True, height=400)
