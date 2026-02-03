import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------
# STREAMLIT CONFIG
# -----------------------------
st.set_page_config(page_title="Lean Conversion Dashboard", layout="wide")
st.title("📊 Lean System Conversion Dashboard")

# -----------------------------
# GOOGLE SHEETS CONNECTION (STREAMLIT CLOUD READY)
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

# Use secrets.toml to load service account
service_account_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

SPREADSHEET_ID = "1KS4PgGii9kcDMKxVtJdPKhaPCabdwsBSC3nkjuRRfvw"
SYSTEM_LOGIC_SHEET = "System_Logic"

client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)
worksheet = spreadsheet.worksheet(SYSTEM_LOGIC_SHEET)

data = worksheet.get_all_records()
df = pd.DataFrame(data)

# -----------------------------
# DATA CLEANING (CRITICAL FIX)
# -----------------------------
df.columns = df.columns.str.strip()
df['Enquiry_ID'] = df['Enquiry_ID'].astype(str).str.strip()
df['Sample_Status'] = df['Sample_Status'].fillna('').astype(str).str.strip().str.lower()
df['Order_Confirmed'] = df['Order_Confirmed'].fillna('').astype(str).str.strip().str.lower()
df['Expected_Value'] = pd.to_numeric(df['Expected_Value'], errors='coerce').fillna(0)
df['Final_Order_Value'] = pd.to_numeric(df['Final_Order_Value'], errors='coerce').fillna(0)

# -----------------------------
# BASE COUNTS
# -----------------------------
total_enquiries = df['Enquiry_ID'].nunique()
sample_approved_df = df[(df['Sample_Status'] == 'approved')]
order_confirmed_df = df[(df['Sample_Status'] == 'approved') & (df['Order_Confirmed'] == 'yes')]

sample_approved_count = sample_approved_df['Enquiry_ID'].nunique()
order_confirmed_count = order_confirmed_df['Enquiry_ID'].nunique()

# -----------------------------
# CONVERSION %
# -----------------------------
lead_to_sample_pct = sample_approved_count / total_enquiries * 100 if total_enquiries else 0
sample_to_order_pct = order_confirmed_count / sample_approved_count * 100 if sample_approved_count else 0
overall_conversion_pct = order_confirmed_count / total_enquiries * 100 if total_enquiries else 0

# -----------------------------
# DASHBOARD METRICS
# -----------------------------
st.subheader("🔁 Conversion Funnel")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Enquiries", total_enquiries)
c2.metric("Sample Approved", sample_approved_count)
c3.metric("Orders Confirmed", order_confirmed_count)
c4.metric("Overall Conversion %", f"{overall_conversion_pct:.2f}%")

st.divider()
c5, c6 = st.columns(2)
c5.metric("Lead → Sample Conversion %", f"{lead_to_sample_pct:.2f}%")
c6.metric("Sample → Order Conversion %", f"{sample_to_order_pct:.2f}%")

# -----------------------------
# VALUE METRICS
# -----------------------------
st.subheader("💰 Value Conversion")
total_expected = df['Expected_Value'].sum()
total_final = order_confirmed_df['Final_Order_Value'].sum()
value_conversion_pct = total_final / total_expected * 100 if total_expected else 0

v1, v2, v3 = st.columns(3)
v1.metric("Total Expected Value", f"₹ {total_expected:,.0f}")
v2.metric("Final Order Value", f"₹ {total_final:,.0f}")
v3.metric("Value Conversion %", f"{value_conversion_pct:.2f}%")

# -----------------------------
# WEEKLY CONVERSION
# -----------------------------
if 'Week' in df.columns:
    st.subheader("📅 Weekly Conversion %")
    weekly_df = df.groupby('Week').agg(
        Enquiries=('Enquiry_ID', 'nunique'),
        Orders=('Order_Confirmed', lambda x: (x=='yes').sum())
    ).reset_index()
    weekly_df['Conversion_%'] = weekly_df['Orders'] / weekly_df['Enquiries'] * 100
    st.dataframe(weekly_df, use_container_width=True)

# -----------------------------
# LEAD SOURCE CONVERSION
# -----------------------------
if 'Lead_Source' in df.columns:
    st.subheader("📍 Lead Source Conversion %")
    lead_df = df.groupby('Lead_Source').agg(
        Enquiries=('Enquiry_ID', 'nunique'),
        Orders=('Order_Confirmed', lambda x: (x=='yes').sum())
    ).reset_index()
    lead_df['Conversion_%'] = lead_df['Orders'] / lead_df['Enquiries'] * 100
    st.dataframe(lead_df, use_container_width=True)

# -----------------------------
# DEBUG VIEW (OPTIONAL)
# -----------------------------
with st.expander("🔍 View System_Logic Data"):
    st.dataframe(df)
