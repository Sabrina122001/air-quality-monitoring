# -*- coding: utf-8 -*-
"""
Streamlit Dashboard - Air Quality Monitoring Stations in France
"""

import pathlib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.io as pio  # for global theme

# ============================================================
# CONFIG – TO CUSTOMIZE
# ============================================================

STUDENT_NAME = "SADDEDINE Sabrina"
PROJECT_TITLE = "Air Quality Monitoring Stations Network in France"
PROJECT_SUBTITLE = (
    "Interactive exploration of monitoring stations: location, area type, "
    "municipalities and activity history."
)
STUDENT_LINKEDIN = "https://www.linkedin.com/in/sabrina-saddedine-348925262/S"
PROF_NAME = "Dr. Mano Mathew"
PROF_LINKEDIN = "https://www.linkedin.com/in/manomathew/"

DATA_PATH = "/Users/oussemaamri/Documents/1st semester/Dataviz/streamlit/fr-2025-d-lcsqa-ineris-20250113.xls"

# ============================================================
# GLOBAL THEME – PLOTLY & STREAMLIT
# ============================================================

# Consistent color palette and style for all charts
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = px.colors.qualitative.Set2

st.set_page_config(
    page_title=PROJECT_TITLE,
    page_icon="🌍",
    layout="wide",
)

# Soft background and nicer cards
st.markdown(
    """
    <style>
    body {
        background-color: #f6f7fb;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
    }
    .main-subtitle {
        font-size: 0.95rem;
        color: #6c757d;
        margin-bottom: 1rem;
    }
    .kpi-card {
        padding: 0.9rem 1.1rem;
        border-radius: 0.9rem;
        border: 1px solid #e5e5e5;
        background: linear-gradient(135deg, #ffffff 0%, #f7f9ff 100%);
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.2rem;
    }
    .kpi-value {
        font-size: 1.4rem;
        font-weight: 700;
    }
    .kpi-caption {
        font-size: 0.75rem;
        color: #999999;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.2rem;
    }
    .section-subtitle {
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DATA LOADING / PREPARATION
# ============================================================

@st.cache_data(show_spinner=True)
def load_data(path: str) -> pd.DataFrame:
    """Load and prepare the air quality monitoring stations dataset."""
    p = pathlib.Path(path)
    if not p.exists():
        st.error(f"Data file not found: {path}")
        st.stop()

    # Read Excel or CSV depending on extension
    if p.suffix.lower() in [".xls", ".xlsx"]:
        # requires xlrd for .xls
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p, sep=";", low_memory=False)

    expected_cols = [
        "GMLID",
        "LocalId",
        "Namespace",
        "Version",
        "NatlStationCode",
        "Name",
        "Municipality",
        "EUStationCode",
        "ActivityBegin",
        "ActivityEnd",
        "Latitude",
        "Longitude",
        "SRSName",
        "Altitude",
        "AltitudeUnit",
        "AreaClassification",
        "BelongsTo",
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        st.warning(f"Missing columns in file: {missing}")

    # Parse dates
    for col in ["ActivityBegin", "ActivityEnd"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Activity years
    if "ActivityBegin" in df.columns:
        df["year_begin"] = df["ActivityBegin"].dt.year.astype("Int64")
    if "ActivityEnd" in df.columns:
        df["year_end"] = df["ActivityEnd"].dt.year.astype("Int64")

    # Station status (active / inactive)
    if "ActivityEnd" in df.columns:
        df["status"] = np.where(df["ActivityEnd"].isna(), "Active", "Inactive")
    else:
        df["status"] = "Unknown"

    # Numeric coordinates & altitude
    for col in ["Latitude", "Longitude", "Altitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Simplified area classification: keep only last part of URI
    if "AreaClassification" in df.columns:
        df["area_class_simple"] = (
            df["AreaClassification"]
            .astype(str)
            .str.split("/")
            .str[-1]
            .str.replace("areaclassification-", "", regex=False)
            .str.replace("-", " ")
        )
    else:
        df["area_class_simple"] = np.nan

    return df


df = load_data(DATA_PATH)

has_geo = "Latitude" in df.columns and "Longitude" in df.columns
has_year = "year_begin" in df.columns and df["year_begin"].notna().any()

# ============================================================
# SIDEBAR – FILTERS & PROJECT INFO
# ============================================================

with st.sidebar:
    st.title("⚙️ Filters")

    # Municipality filter
    if "Municipality" in df.columns:
        municipalities = (
            df["Municipality"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )
    else:
        municipalities = []
    selected_municipalities = st.multiselect(
        "Municipality",
        options=municipalities,
        default=[],
    )

    # Area type filter
    area_classes = (
        df["area_class_simple"].dropna().sort_values().unique().tolist()
        if "area_class_simple" in df.columns
        else []
    )
    selected_area = st.multiselect(
        "Area type",
        options=area_classes,
        default=[],
    )

    # Status filter
    status_choices = (
        df["status"].dropna().sort_values().unique().tolist()
        if "status" in df.columns
        else ["Active", "Inactive"]
    )
    selected_status = st.multiselect(
        "Station status",
        options=status_choices,
        default=status_choices,
    )

    # Year filter
    if has_year:
        min_year = int(df["year_begin"].min())
        max_year = int(df["year_begin"].max())
        year_range = st.slider(
            "Start year of activity",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
            step=1,
        )
    else:
        year_range = None

    # Altitude filter
    if "Altitude" in df.columns and df["Altitude"].notna().any():
        min_alt = float(df["Altitude"].min())
        max_alt = float(df["Altitude"].max())
        alt_range = st.slider(
            "Altitude (m)",
            min_value=float(min_alt),
            max_value=float(max_alt),
            value=(float(min_alt), float(max_alt)),
            step=1.0,
        )
    else:
        alt_range = None

    st.markdown("---")
    st.header("Project information")
    st.markdown(f"**Student:** {STUDENT_NAME}")
    st.markdown(f"**Project:** {PROJECT_TITLE}")
    if STUDENT_LINKEDIN:
        st.markdown(f"[Student LinkedIn]({STUDENT_LINKEDIN})")
    st.markdown(f"**Instructor:** {PROF_NAME}")
    if PROF_LINKEDIN:
        st.markdown(f"[Instructor LinkedIn]({PROF_LINKEDIN})")
    st.markdown("---")
    st.caption("Source: LCSQA / INERIS – station metadata (local file).")

# ============================================================
# APPLY FILTERS
# ============================================================

df_filtered = df.copy()

if selected_municipalities:
    df_filtered = df_filtered[df_filtered["Municipality"].isin(selected_municipalities)]

if selected_area:
    df_filtered = df_filtered[df_filtered["area_class_simple"].isin(selected_area)]

if selected_status:
    df_filtered = df_filtered[df_filtered["status"].isin(selected_status)]

if has_year and year_range is not None:
    df_filtered = df_filtered[
        df_filtered["year_begin"].between(year_range[0], year_range[1])
        | df_filtered["year_begin"].isna()
    ]

if alt_range is not None and "Altitude" in df_filtered.columns:
    df_filtered = df_filtered[
        df_filtered["Altitude"].between(alt_range[0], alt_range[1])
        | df_filtered["Altitude"].isna()
    ]

if df_filtered.empty:
    st.warning("No station matches the selected filters.")
    st.stop()

# ============================================================
# HEADER
# ============================================================

st.markdown(f'<div class="main-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="main-subtitle">{PROJECT_SUBTITLE}</div>',
    unsafe_allow_html=True,
)

# ============================================================
# KPIs (with an extra indicator: median lifetime)
# ============================================================

total_stations = len(df_filtered)
nb_muni = df_filtered["Municipality"].nunique() if "Municipality" in df_filtered.columns else np.nan
active_share = (
    (df_filtered["status"] == "Active").mean() * 100 if "status" in df_filtered.columns else np.nan
)
avg_alt = df_filtered["Altitude"].mean() if "Altitude" in df_filtered.columns else np.nan

# Median station lifetime in years (robust to timezones and missing values)
median_life = np.nan
if "ActivityBegin" in df_filtered.columns:
    begin = pd.to_datetime(df_filtered["ActivityBegin"], errors="coerce", utc=True)
    begin = begin.dt.tz_convert(None)  # drop timezone

    if "ActivityEnd" in df_filtered.columns:
        end = pd.to_datetime(df_filtered["ActivityEnd"], errors="coerce", utc=True)
        end = end.dt.tz_convert(None)
    else:
        end = pd.Series(pd.NaT, index=begin.index)

    today = pd.Timestamp.today()
    end = end.fillna(today)

    life_days = (end - begin).dt.days
    life_years = life_days[life_days >= 0] / 365.25

    if not life_years.empty:
        median_life = life_years.median()

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.markdown('<div class="kpi-label">Filtered stations</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-value">{total_stations:,}</div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-caption">After applying filters</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.markdown('<div class="kpi-label">Covered municipalities</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-value">{nb_muni}</div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-caption">Territorial diversity</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.markdown('<div class="kpi-label">Active stations</div>', unsafe_allow_html=True)
    if not np.isnan(active_share):
        st.markdown(f'<div class="kpi-value">{active_share:.1f} %</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="kpi-value">N/A</div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-caption">ActivityEnd missing = active</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.markdown('<div class="kpi-label">Average altitude</div>', unsafe_allow_html=True)
    if not np.isnan(avg_alt):
        st.markdown(f'<div class="kpi-value">{avg_alt:.0f} m</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="kpi-value">N/A</div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-caption">Stations with known altitude</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c5:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.markdown('<div class="kpi-label">Median lifetime</div>', unsafe_allow_html=True)
    if not np.isnan(median_life):
        st.markdown(f'<div class="kpi-value">{median_life:.1f} yrs</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="kpi-value">N/A</div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-caption">From ActivityBegin to ActivityEnd / today</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# TABS TO STRUCTURE THE APP
# ============================================================

tab_map, tab_typo, tab_hist, tab_detail, tab_doc = st.tabs(
    ["🗺️ Map", "🏙️ Typology & municipalities", "⏳ History", "📋 Detail & data quality", "📘 Documentation"]
)

# ============================================================
# TAB 1 – MAP
# ============================================================

with tab_map:
    st.markdown('<div class="section-title">Where are the stations located?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Interactive map of air quality monitoring stations, colored by area type.</div>',
        unsafe_allow_html=True,
    )

    if has_geo:
        df_geo = df_filtered.dropna(subset=["Latitude", "Longitude"])
        if not df_geo.empty:
            center_lat = df_geo["Latitude"].mean()
            center_lon = df_geo["Longitude"].mean()

            fig_map = px.scatter_mapbox(
                df_geo,
                lat="Latitude",
                lon="Longitude",
                color="area_class_simple",
                hover_name="Name",
                hover_data={
                    "Municipality": True if "Municipality" in df_geo.columns else False,
                    "Altitude": True if "Altitude" in df_geo.columns else False,
                    "status": True if "status" in df_geo.columns else False,
                },
                zoom=5,
                center={"lat": center_lat, "lon": center_lon},
                height=550,
            )
            fig_map.update_layout(
                mapbox_style="carto-positron",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_map, use_container_width=True)

            st.markdown("""
  
This map displays the spatial distribution of France’s air quality monitoring stations.  
Most stations are located in **urban and suburban areas**, where population density and pollution sources (traffic, industries) are highest.  
Rural stations exist but are more dispersed and typically monitor background pollution levels.
""")
        else:
            st.info("Geographical coordinates are missing for the filtered stations.")
    else:
        st.info("Latitude/Longitude columns are not available in the file.")

# ============================================================
# TAB 2 – TYPOLOGY & MUNICIPALITIES
# ============================================================

with tab_typo:
    st.markdown(
        '<div class="section-title">Which area types dominate? Which municipalities are most covered?</div>',
        unsafe_allow_html=True,
    )
    col_zones, col_muni = st.columns(2)

    # Area type distribution
    with col_zones:
        st.markdown(
            '<div class="section-subtitle">Distribution of stations by area type.</div>',
            unsafe_allow_html=True,
        )
        if "area_class_simple" in df_filtered.columns:
            zone_counts = (
                df_filtered["area_class_simple"]
                .dropna()
                .value_counts()
                .reset_index()
            )
            zone_counts.columns = ["Area type", "Number of stations"]

            fig_zone = px.bar(
                zone_counts,
                x="Area type",
                y="Number of stations",
                labels={"Number of stations": "Number of stations"},
            )
            fig_zone.update_layout(
                xaxis_tickangle=-20,
                margin=dict(l=10, r=10, t=10, b=60),
            )
            st.plotly_chart(fig_zone, use_container_width=True)

            st.markdown("""
 
The distribution of area types shows how the monitoring network is structured.  
- **Urban stations** measure population exposure and traffic-related pollution.  
- **Suburban stations** monitor mixed residential/industrial areas.  
- **Rural and rural-regional stations** provide background measurements used for national and European reporting.

A dominance of urban/suburban stations is expected because human exposure is the key regulatory priority.
""")
        else:
            st.info("Area classification is not available.")

    # Top municipalities
    with col_muni:
        st.markdown(
            '<div class="section-subtitle">Top municipalities by number of stations.</div>',
            unsafe_allow_html=True,
        )
        if "Municipality" in df_filtered.columns:
            muni_counts = (
                df_filtered["Municipality"]
                .dropna()
                .value_counts()
                .reset_index()
                .head(15)
            )
            muni_counts.columns = ["Municipality", "Number of stations"]

            fig_muni = px.bar(
                muni_counts,
                x="Number of stations",
                y="Municipality",
                orientation="h",
                labels={
                    "Number of stations": "Number of stations",
                    "Municipality": "Municipality",
                },
            )
            fig_muni.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_muni, use_container_width=True)

            st.markdown("""

 
This chart highlights the municipalities with the highest number of monitoring stations.  
Large cities or industrial towns typically have more stations due to:  
- higher population exposure  
- complex pollution sources  
- regulatory requirements for dense monitoring around sensitive zones.
""")
        else:
            st.info("Municipality column is not available.")

    # Extra indicator: status distribution (Active vs Inactive)
    st.markdown(
        '<div class="section-title">How many stations are active vs inactive?</div>',
        unsafe_allow_html=True,
    )
    if "status" in df_filtered.columns:
        status_counts = (
            df_filtered["status"]
            .value_counts()
            .reset_index()
        )
        status_counts.columns = ["Status", "Number of stations"]

        fig_status = px.pie(
            status_counts,
            names="Status",
            values="Number of stations",
            hole=0.3,
        )
        fig_status.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_status, use_container_width=True)

        st.markdown("""
**Interpretation:**  
**Active stations** are sites still operating today or whose `ActivityEnd` is missing (meaning they were never officially closed).  
**Inactive stations** stopped reporting after their `ActivityEnd` date.

A high proportion of inactive stations is normal:  
stations are regularly relocated or modernized as new regulations and technologies appear.
""")
    else:
        st.info("Station status is not available.")

# ============================================================
# TAB 3 – HISTORY
# ============================================================

with tab_hist:
    if has_year:
        st.markdown(
            '<div class="section-title">How has the network evolved over time?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-subtitle">Number of stations put into service by start year of activity.</div>',
            unsafe_allow_html=True,
        )

        df_year = df_filtered.dropna(subset=["year_begin"])
        if not df_year.empty:
            year_counts = (
                df_year.groupby("year_begin")
                .size()
                .reset_index(name="Number of stations")
                .sort_values("year_begin")
            )

            fig_year = px.line(
                year_counts,
                x="year_begin",
                y="Number of stations",
                markers=True,
                labels={"year_begin": "Start year of activity"},
            )
            fig_year.update_traces(mode="lines+markers")
            fig_year.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_year, use_container_width=True)

            st.markdown("""
**Interpretation of the peak around 2000:**  
The strong increase in station installations around the year **2000** corresponds to major regulatory changes:
- implementation of the first EU Air Quality Directives (1996 & 1999)  
- modernization of national monitoring networks (AASQA & LCSQA/INERIS)  
- new mandatory pollutants (NO₂, PM₁₀, O₃, SO₂, benzene…)

This period required a rapid expansion of the monitoring network.  
After 2010, the system reached maturity, so new installations slowed down.
""")
        else:
            st.info("Start dates of activity are not sufficiently available to display the curve.")
    else:
        st.info("Start years of activity are not available.")

# ============================================================
# TAB 4 – DETAIL & DATA QUALITY
# ============================================================

with tab_detail:
    st.markdown(
        '<div class="section-title">Detailed view of filtered stations</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Filterable table with key characteristics.</div>',
        unsafe_allow_html=True,
    )

    cols_table = [
        "NatlStationCode",
        "EUStationCode",
        "Name",
        "Municipality",
        "ActivityBegin",
        "ActivityEnd",
        "status",
        "Latitude",
        "Longitude",
        "Altitude",
        "area_class_simple",
        "BelongsTo",
    ]

    available_cols = [c for c in cols_table if c in df_filtered.columns]

    st.dataframe(
        df_filtered[available_cols]
        .sort_values(["Municipality", "Name"])
        .reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        '<div class="section-title">Data quality</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Missing value rate for selected key variables.</div>',
        unsafe_allow_html=True,
    )

    quality_cols = [
        "ActivityBegin",
        "ActivityEnd",
        "Latitude",
        "Longitude",
        "Altitude",
        "AreaClassification",
    ]
    quality_cols = [c for c in quality_cols if c in df.columns]

    if quality_cols:
        missing = df[quality_cols].isna().mean().reset_index()
        missing.columns = ["Variable", "Missing rate"]
        missing["Missing rate"] = missing["Missing rate"] * 100

        fig_missing = px.bar(
            missing,
            x="Variable",
            y="Missing rate",
            labels={"Missing rate": "Missing rate (%)"},
        )
        fig_missing.update_layout(
            xaxis_tickangle=-30,
            margin=dict(l=10, r=10, t=10, b=60),
        )
        st.plotly_chart(fig_missing, use_container_width=True)

    st.info(
        """  
Variables with high missing rates must be interpreted carefully in the rest of the dashboard.  
For example, missing coordinates mean some stations are not shown on the map, and missing dates affect the history analysis.
"""
    )

# ============================================================
# TAB 5 – DOCUMENTATION
# ============================================================

with tab_doc:
    st.markdown("## Dataset Documentation & Interpretation Guide")

    st.markdown("""
### 1. What this dataset represents
This dataset contains **metadata about air quality monitoring stations in France**, provided by **LCSQA / INERIS**.  
It does **not** contain pollutant measurements, only station characteristics:

- Station identifiers  
- Names and municipalities  
- Geographic coordinates  
- Area classification (urban / suburban / rural)  
- Installation and shutdown dates  
- Administrative network information

The goal is to understand **how the monitoring network is structured**, not pollution levels.

---

### 2. What is an “Active” vs “Inactive” station?
- **Active** → no `ActivityEnd` date → the station is still running today  
- **Inactive** → the station was closed on the `ActivityEnd` date  

Stations are regularly:
- relocated  
- upgraded  
- reconfigured according to new regulations  

So a mix of active and inactive stations is completely normal for a mature network.

---

### 3. What is area classification?
These categories come from the European Air Quality Network:

- **Urban** → city center, high population exposure  
- **Suburban** → residential areas mixed with industrial/traffic influence  
- **Rural** → countryside, low emissions  
- **Rural-regional** → background pollution representative of wide regions  

These categories are essential for **regulatory reporting** and for comparing stations across Europe.

---

### 4. Why is there a peak in station installations around 1998–2002?
This peak is linked to:

1. **EU Air Quality Directives (1996 & 1999)**  
2. New mandatory pollutants (e.g. NO₂, PM₁₀, O₃, benzene, SO₂)  
3. **Modernization of the French network** (AASQA, LCSQA, INERIS)  
4. The need to build a harmonized and dense monitoring network in urban areas  

As a result, many new stations were installed around the year 2000.  
After that, the network reached **maturity**, and the priority shifted from new installations to maintenance and upgrades.

---

### 5. How to interpret the dashboard
- **Map** → where the network is dense or sparse; which regions are more monitored  
- **Typology** → which types of areas (urban vs rural) are prioritized  
- **Municipalities** → which cities host the highest number of stations  
- **History** → how regulations and policies shaped the network over time  
- **Data quality** → where missing values can bias interpretation

---

  """)



