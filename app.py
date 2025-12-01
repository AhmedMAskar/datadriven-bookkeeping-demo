import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

# ----- BASIC CONFIG -----
st.set_page_config(
    page_title="DataDriven Bookkeeping Demo",
    layout="centered",
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
IND
