import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

DATA_FILE = "311_2025_dashboard.csv"

st.set_page_config(page_title="2025 311 Dashboard", layout="wide")


# ---------------------------------------------------------------
# 1. Load the data (cached so it only reads the CSV once)
# ---------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    df["request_date"] = pd.to_datetime(df["request_date"], errors="coerce")
    return df


df = load_data()

# ---------------------------------------------------------------
# 2. Title
# ---------------------------------------------------------------
st.title("2025 311 Service Requests Dashboard")
st.write(
    "This dashboard summarizes 311 service requests made in 2025. "
    "Use the sidebar to choose a start and end date and, optionally, filter by agency. "
    "All metrics and charts update to match your selections."
)

# ---------------------------------------------------------------
# 3. Date controls (these replace START_DATE and END_DATE)
# ---------------------------------------------------------------
min_date = df["request_date"].min().date()
max_date = df["request_date"].max().date()

# Default range when the app opens (same as START_DATE / END_DATE in the notebook).
# max() and min() keep the defaults inside the dates that exist in the data.
default_start = max(min_date, pd.to_datetime("2025-01-01").date())
default_end = min(max_date, pd.to_datetime("2025-04-30").date())

st.sidebar.header("Filters")
selected = st.sidebar.date_input(
    "Date range",
    value=(default_start, default_end),
    min_value=min_date,
    max_value=max_date,
)

# Second control: filter by agency (leave empty to include all agencies)
agency_options = sorted(df["agency_responsible"].dropna().unique())
selected_agencies = st.sidebar.multiselect(
    "Agency (leave empty for all)",
    options=agency_options,
)

# date_input returns a tuple of 2 dates once both are picked,
# but only 1 date while the user is mid-selection.
if len(selected) != 2:
    st.info("Pick both a start date and an end date in the sidebar.")
    st.stop()

start_date = pd.to_datetime(selected[0])
end_date = pd.to_datetime(selected[1])

# ---------------------------------------------------------------
# 4. Filter the DataFrame (same logic as the notebook)
# ---------------------------------------------------------------
filtered_df = df[
    (df["request_date"] >= start_date) &
    (df["request_date"] <= end_date)
].copy()

# Apply the agency filter only if the user picked at least one agency
if selected_agencies:
    filtered_df = filtered_df[filtered_df["agency_responsible"].isin(selected_agencies)]

# ---------------------------------------------------------------
# 5. Summary metrics
# ---------------------------------------------------------------
if filtered_df.empty:
    st.warning("No requests found for these filters. Try a wider date range or fewer agencies.")
    st.stop()

st.caption(
    f"Showing requests from {start_date:%b %d, %Y} to {end_date:%b %d, %Y}"
    + (f" for {len(selected_agencies)} selected agenc{'y' if len(selected_agencies) == 1 else 'ies'}"
       if selected_agencies else " for all agencies")
)

total_requests = len(filtered_df)
num_service_types = filtered_df["service_name"].nunique()
num_zip_codes = filtered_df["zipcode"].nunique()
percent_closed = (
    filtered_df["status"].astype(str).str.lower().eq("closed").mean() * 100
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total requests", f"{total_requests:,}")
m2.metric("Service types", f"{num_service_types:,}")
m3.metric("ZIP codes", f"{num_zip_codes:,}")
m4.metric("Percent closed", f"{percent_closed:.1f}%")

# ---------------------------------------------------------------
# 6. Charts (2 rows of 2)
# ---------------------------------------------------------------

# ----- Row 1: the two sample charts from the notebook -----
col1, col2 = st.columns(2)

# Chart 1: Top 10 request types
with col1:
    top_requests = (
        filtered_df["service_name"]
        .value_counts()
        .head(10)
        .sort_values()
    )

    figA, axA = plt.subplots(figsize=(8, 5))
    top_requests.plot(kind="barh", ax=axA, title="Top 10 Types of 311 Requests")
    axA.set_xlabel("Number of Requests")
    axA.set_ylabel("Service Type")
    figA.tight_layout()
    st.pyplot(figA)

# Chart 2: Requests over time
with col2:
    requests_by_day = (
        filtered_df
        .groupby("request_date")
        .size()
    )

    figB, axB = plt.subplots(figsize=(8, 5))
    requests_by_day.plot(kind="line", ax=axB, title="311 Requests Over Time")
    axB.set_xlabel("Request Date")
    axB.set_ylabel("Number of Requests")
    figB.tight_layout()
    st.pyplot(figB)

# ----- Row 2: the two charts added later (agencies and ZIP codes) -----
col3, col4 = st.columns(2)

# Chart 3: Top 10 agencies
with col3:
    top_agencies = (
        filtered_df["agency_responsible"]
        .value_counts()
        .head(10)
        .sort_values()
    )

    fig1, ax1 = plt.subplots(figsize=(8, 5))
    top_agencies.plot(kind="barh", ax=ax1, title="Top 10 Agencies Handling 311 Requests")
    ax1.set_xlabel("Number of Requests")
    ax1.set_ylabel("Agency")
    fig1.tight_layout()
    st.pyplot(fig1)

# Chart 4: Top 10 ZIP codes
with col4:
    # zipcode often loads as a float (e.g. 94110.0), so clean it into a plain string
    zips = (
        pd.to_numeric(filtered_df["zipcode"], errors="coerce")
        .dropna()
        .astype(int)
        .astype(str)
    )
    top_zips = zips.value_counts().head(10).sort_values()

    fig2, ax2 = plt.subplots(figsize=(8, 5))
    top_zips.plot(kind="barh", ax=ax2, title="Top 10 ZIP Codes by Number of 311 Requests")
    ax2.set_xlabel("Number of Requests")
    ax2.set_ylabel("ZIP Code")
    fig2.tight_layout()
    st.pyplot(fig2)
