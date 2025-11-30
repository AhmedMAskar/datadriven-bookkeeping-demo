import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

# ----- BASIC CONFIG -----
st.set_page_config(
    page_title="DataDriven Bookkeeping – Multi-Industry Financial Demo",
    layout="wide"
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

    # Use Profit_Current if available, else Revenue_Current
    value_col = "Profit_Current" if "Profit_Current" in sdf.columns else "Revenue_Current"

    q20 = sdf[value_col].quantile(0.2)
    q80 = sdf[value_col].quantile(0.8)

    hot = sdf[sdf[value_col] >= q80]
    cold = sdf[sdf[value_col] <= q20]

    def fmt_zip_block(df_slice: pd.DataFrame) -> str:
        rows = []
        for _, row in df_slice.head(4).iterrows():
            rows.append(f"{int(row['Zip'])} ({row['City']})")
        return ", ".join(rows)

    hot_txt = fmt_zip_block(hot)
    cold_txt = fmt_zip_block(cold)

    pieces = []
    if hot_txt:
        pieces.append(
            f"- **Hot spots** for {industry.lower()} revenue/profit are clustering around **{hot_txt}**."
        )
    if cold_txt:
        pieces.append(
            f"- **Cold spots** (underperforming ZIPs) include **{cold_txt}**."
        )

    if not pieces:
        return "Performance looks fairly even across ZIP codes with no strong hot or cold pockets."

    return "\n".join(pieces)


# ---------- SIDEBAR ----------

st.sidebar.title("DataDriven Bookkeeping Demo")

industry = st.sidebar.selectbox(
    "Sample client type",
    list(INDUSTRY_FILES.keys())
)

page = st.sidebar.radio(
    "View",
    ["Profit & Loss", "Insights", "Spatial", "Trends", "Balance Sheet", "Cash Flow"]
)

filename = INDUSTRY_FILES[industry]
df = load_pl_data(filename)
revenues, cogs, opex, summary = split_sections(df)

# Pre-calc for several views
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
    st.title(f"Profit & Loss – {industry}")
    st.caption("Demo only – sample numbers to show how DataDriven Bookkeeping can present your financials.")

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Total Revenue (Current)",
        f"${total_rev_cur:,.0f}",
        f"${total_rev_cur - total_rev_prev:,.0f}"
    )
    k2.metric(
        "Gross Profit",
        f"${gross_profit:,.0f}",
        f"{gross_margin*100:,.1f}% margin"
    )
    k3.metric(
        "Operating Profit",
        f"${operating_profit:,.0f}",
        f"{oper_margin*100:,.1f}% margin"
    )
    k4.metric(
        "Net Income",
        f"${net_income:,.0f}",
        f"{net_margin*100:,.1f}% margin"
    )

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
        st.dataframe(df)

# ---------- INSIGHTS PAGE ----------

elif page == "Insights":
    st.title(f"Commentary & Insights – {industry}")

    net_income_cur = get_summary_value(summary, "NET INCOME (LOSS)")
    net_income_prev = summary.loc["NET INCOME (LOSS)", "Prior Period"] if "NET INCOME (LOSS)" in summary.index else 0
    delta = net_income_cur - net_income_prev
    pct = (delta / net_income_prev * 100) if net_income_prev else None

    st.subheader("High-level trend")
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

# ---------- SPATIAL PAGE ----------

elif page == "Spatial":
    st.title(f"Where Your Clients Are – {industry}")
    spatial_file = INDUSTRY_SPATIAL_FILES[industry]
    sdf = load_csv(spatial_file)

    # Basic metrics
    total_new = sdf["New_Customers"].sum()
    total_visits = sdf["Visits"].sum()
    total_rev = sdf["Revenue_Current"].sum()
    total_profit = sdf["Profit_Current"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("New Customers (Period)", f"{total_new:,}")
    c2.metric("Total Visits / Jobs", f"{total_visits:,}")
    c3.metric("Revenue (Current Period)", f"${total_rev:,.0f}")
    c4.metric("Estimated Profit (Current)", f"${total_profit:,.0f}")

    st.markdown("---")

    # Map
    st.subheader("ZIP-Level Performance Map")
    fig_map = px.scatter_geo(
        sdf,
        lat="Latitude",
        lon="Longitude",
        color="Profit_Current",
        size="Revenue_Current",
        hover_name="Zip",
        hover_data=["City", "New_Customers", "Visits", "Revenue_Current", "Profit_Current"],
        title="Hot & Cold ZIP Codes (size = revenue, color = profit)"
    )
    fig_map.update_geos(fitbounds="locations", showcountries=False, showland=True, lataxis_showgrid=True, lonaxis_showgrid=True)
    fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("Narrative Summary")
    st.markdown(generate_spatial_commentary(industry, sdf))

    with st.expander("Underlying ZIP Table"):
        st.dataframe(sdf)

# ---------- TRENDS PAGE ----------

elif page == "Trends":
    st.title(f"Monthly Trends – {industry}")
    trend_file = INDUSTRY_TREND_FILES[industry]
    tdf = load_csv(trend_file)

    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    if "Month" in tdf.columns:
        tdf["Month"] = pd.Categorical(tdf["Month"], categories=month_order, ordered=True)
        tdf = tdf.sort_values("Month")

    st.subheader("Revenue & Net Income Over Time")
    fig_trend = px.line(
        tdf,
        x="Month",
        y=["Total_Revenue", "Net_Income"],
        markers=True,
        title="Monthly Revenue & Net Income"
    )
    fig_trend.update_layout(yaxis_title="Amount ($)", legend_title="")
    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("Gross Profit vs Operating Expenses")
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
        st.dataframe(tdf)

# ---------- BALANCE SHEET PAGE ----------

elif page == "Balance Sheet":
    st.title(f"Balance Sheet – {industry}")
    bs_file = INDUSTRY_BS_FILES[industry]
    bs = load_csv(bs_file)

    total_assets = bs.loc[bs["Line Item"] == "TOTAL ASSETS", "Current Period"].iloc[0]
    total_liab = bs.loc[bs["Line Item"] == "TOTAL LIABILITIES", "Current Period"].iloc[0]
    total_equity = bs.loc[bs["Line Item"] == "TOTAL EQUITY", "Current Period"].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Assets", f"${total_assets:,.0f}")
    c2.metric("Total Liabilities", f"${total_liab:,.0f}")
    c3.metric("Total Equity", f"${total_equity:,.0f}")

    st.markdown("---")
    st.subheader("Balance Sheet Detail")
    st.dataframe(bs)

# ---------- CASH FLOW PAGE ----------

elif page == "Cash Flow":
    st.title(f"Cash Flow – {industry}")
    cf_file = INDUSTRY_CF_FILES[industry]
    cf = load_csv(cf_file)

    beg = cf.loc[cf["Line Item"] == "Beginning Cash", "Current Period"].iloc[0]
    end = cf.loc[cf["Line Item"] == "Ending Cash", "Current Period"].iloc[0]
    delta = end - beg

    c1, c2, c3 = st.columns(3)
    c1.metric("Beginning Cash", f"${beg:,.0f}")
    c2.metric("Ending Cash", f"${end:,.0f}", f"${delta:,.0f}")
    c3.metric("Net Cash Change", f"${delta:,.0f}")

    st.markdown("---")

    st.subheader("Cash Flow by Section")
    st.dataframe(cf)
