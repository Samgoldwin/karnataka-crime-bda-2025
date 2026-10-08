import streamlit as st
import pandas as pd
import mysql.connector

st.set_page_config(page_title="Crime Analytics – Karnataka (2025)", layout="wide")

@st.cache_data(ttl=300)
def query_mysql(sql, params=None):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_PASSWORD",
        database="crime_analytics",
        autocommit=True
    )
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df

# Sidebar filters
df_d = query_mysql("SELECT district FROM district_master_2025 ORDER BY district")
districts = ["All"] + df_d["district"].tolist()
sel_d = st.sidebar.selectbox("District", districts)
years = [2025, 2024, 2023]
sel_y = st.sidebar.selectbox("Year", years, index=0)

# KPIs
if sel_d == "All":
    kpi = query_mysql("""
        SELECT
          SUM(total_cognizable_cases_2025) AS total_cases,
          ROUND(AVG(total_crime_rate_2025),2) AS avg_crime_rate,
          ROUND(AVG(total_chargesheeting_rate_2025),2) AS avg_cs_rate,
          ROUND(AVG(conviction_rate_ipc_bns_pct_2025),2) AS avg_conviction_pct
        FROM district_master_2025
    """)
else:
    kpi = query_mysql("""
        SELECT total_cognizable_cases_2025 AS total_cases,
               total_crime_rate_2025 AS avg_crime_rate,
               total_chargesheeting_rate_2025 AS avg_cs_rate,
               conviction_rate_ipc_bns_pct_2025 AS avg_conviction_pct
        FROM district_master_2025
        WHERE district=%s
    """, (sel_d,))

c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Cognizable Cases (2025)", int(kpi.iloc[0]["total_cases"]) if not kpi.empty and kpi.iloc[0]["total_cases"] is not None else 0)
c2.metric("Avg/Dist Crime Rate (per 100000)", float(kpi.iloc[0]["avg_crime_rate"]) if not kpi.empty and kpi.iloc[0]["avg_crime_rate"] is not None else 0)
c3.metric("Avg Chargesheeting %", float(kpi.iloc[0]["avg_cs_rate"]) if not kpi.empty and kpi.iloc[0]["avg_cs_rate"] is not None else 0)
c4.metric("Conviction % (IPC/BNS)", float(kpi.iloc[0]["avg_conviction_pct"]) if not kpi.empty and kpi.iloc[0]["avg_conviction_pct"] is not None else 0)

st.subheader("Top Districts by Total Crime Rate (2025)")
top = query_mysql("""
    SELECT district, total_crime_rate_2025, total_cognizable_cases_2025, population_lakhs_2025
    FROM district_master_2025
    ORDER BY total_crime_rate_2025 DESC
    LIMIT 15
""")
st.bar_chart(top.set_index("district")["total_crime_rate_2025"])

st.subheader("Crime by Domain")
if sel_d == "All":
    dom = query_mysql("""
        SELECT domain, SUM(cases) AS cases
        FROM crime_district_trends
        WHERE year=%s AND domain!='total_cognizable'
        GROUP BY domain
        ORDER BY cases DESC
    """, (sel_y,))
else:
    dom = query_mysql("""
        SELECT domain, cases
        FROM crime_district_trends
        WHERE district=%s AND year=%s AND domain!='total_cognizable'
        ORDER BY cases DESC
    """, (sel_d, sel_y))
st.bar_chart(dom.set_index("domain")["cases"])

st.subheader("Total Cognizable Cases – Time Series")
if sel_d == "All":
    ts = query_mysql("""
        SELECT year, SUM(cases) AS total_cases
        FROM crime_district_trends
        WHERE domain='total_cognizable'
        GROUP BY year
        ORDER BY year
    """)
else:
    ts = query_mysql("""
        SELECT year, cases AS total_cases
        FROM crime_district_trends
        WHERE domain='total_cognizable' AND district=%s
        ORDER BY year
    """, (sel_d,))
st.line_chart(ts.set_index("year")["total_cases"])

st.subheader("Property Recovery % by District (2025)")
prop = query_mysql("""
    SELECT district, recovery_pct_2025
    FROM property_stolen_recovered_district_2023_2025
    ORDER BY recovery_pct_2025 DESC
""")
st.bar_chart(prop.set_index("district")["recovery_pct_2025"])

st.subheader("Recidivism % (IPC/BNS) – 2025")
rec = query_mysql("""
    SELECT district, recidivism_pct
    FROM recidivism_ipc_district_2025
    ORDER BY recidivism_pct DESC
""")
st.bar_chart(rec.set_index("district")["recidivism_pct"])
