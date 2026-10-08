from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import sqlite3, textwrap, os

pdf_path = r'C:\Users\David\PROJECTS\bigdataanalytics\Project_Report_Crime_Analytics.pdf'
c = canvas.Canvas(pdf_path, pagesize=A4)
w,h = A4

def title(t,y):
    c.setFont('Helvetica-Bold',16); c.drawString(2*cm,y,t)

def para(text,y,size=10,leading=14):
    c.setFont('Helvetica',size)
    for line in textwrap.wrap(text,90):
        c.drawString(2*cm,y,line); y-=leading
    return y

y = h-2*cm
title('Crime Analytics – Big Data Project Report', y); y-=cm
y = para('Crime in Karnataka 2025 – End-to-End Big Data Pipeline (HDFS/PySpark + MySQL/SQLite + Streamlit)', y); y-=10

title('1. Objectives', y); y-=cm
y = para('- Distributed ETL: HDFS -> PySpark -> Spark SQL -> MySQL/SQLite -> Streamlit', y)
y = para('- Extract/clean/normalize NCRB-style district-level crime data (Karnataka 2025)', y)
y = para('- Compute KPIs/rates, trends, domain-wise analysis for data-driven decisions', y); y-=10

title('2. Data Sources & Validation', y); y-=cm
y = para('Source: Crime in Karnataka 2025 (Govt. of Karnataka Police Department)', y)
y = para('Extraction: pdfplumber -> 26 CSVs in crime_karnataka_2025_csv/', y)
y = para('Validation: 1,521 trend rows, 39 districts, 2023–2025; 13 normalized tables', y)
y = para('Reference artifacts: CSV zip, DB (crime_analytics.db), schema.sql, data_dictionary.csv', y); y-=10

title('3. Architecture & Methodology', y); y-=cm
y = para('Pipeline: HDFS (raw/processed) -> PySpark (clean/typecast/dedup) -> Spark SQL (aggregations) -> SQLite/MySQL (results) -> Streamlit (UI)', y)
y = para('Components: scripts/hdfs_upload.sh, pyspark_crime_analytics.py, load_to_sqlite.py, streamlit_app_sqlite.py, streamlit_app.py, schema.sql', y); y-=10

if y < 5*cm: c.showPage(); y=h-2*cm
title('4. Analytics, Insights & Interpretation', y); y-=cm
con = sqlite3.connect(r'C:\Users\David\PROJECTS\bigdataanalytics\crime_analytics.db'); cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM crime_district_trends"); y=para(f'- Fact records: {cur.fetchone()[0]} (domain x district x year)', y)
cur.execute("SELECT COUNT(DISTINCT district) FROM crime_district_trends WHERE domain='total_cognizable'"); y=para(f'- Coverage: {cur.fetchone()[0]} districts (2023–2025)', y)
cur.execute("SELECT MIN(year),MAX(year) FROM crime_district_trends"); a,b=cur.fetchone(); y=para(f'- Period: {a}–{b}', y)
cur.execute("SELECT year,SUM(cases) FROM crime_district_trends WHERE domain='total_cognizable' GROUP BY year ORDER BY year"); rows=cur.fetchall(); ts=', '.join(f'{r[0]}:{r[1]}' for r in rows); y=para(f'- Total cognizable cases (trend): {ts}', y)
cur.execute("SELECT district,total_crime_rate_2025 FROM district_master_2025 ORDER BY total_crime_rate_2025 DESC LIMIT 5"); top5=cur.fetchall(); t='; '.join(f'{d} ({r})' for d,r in top5); y=para(f'- Top 5 by total crime rate (2025): {t}', y)
cur.execute("SELECT domain,SUM(cases) FROM crime_district_trends WHERE year=2025 AND domain!='total_cognizable' GROUP BY domain ORDER BY SUM(cases) DESC LIMIT 5"); dom=cur.fetchall(); dlist='; '.join(f'{dm} ({c})' for dm,c in dom); y=para(f'- Top 5 domains (2025): {dlist}', y)
cur.execute("SELECT ROUND(AVG(recovery_pct_2025),2) FROM property_stolen_recovered_district_2023_2025"); rp=cur.fetchone()[0] or 0; y=para(f'- Avg property recovery % (2025): {rp} (enforcement effectiveness)', y)
cur.execute("SELECT ROUND(AVG(recidivism_pct),2) FROM recidivism_ipc_district_2025"); rc=cur.fetchone()[0] or 0; y=para(f'- Avg IPC/BNS recidivism % (2025): {rc} (repeat offenders)', y)
con.close()
if y < 5*cm: c.showPage(); y=h-2*cm
y=para('- 5Vs of Big Data: Volume (structured fact), Variety (multiple crime domains), Velocity (batch ETL), Veracity (cleaned/typed/deduped), Value (actionable KPIs)', y)
y=para('- Insights: Inter-district variation indicates localized drivers; domain mix informs resource allocation; recovery % and recidivism % measure outcomes, not just incidents', y); y-=10

title('5. Conclusion & Future Scope', y); y-=cm
y=para('End-to-end big data analytics pipeline implemented, validated, and documented. Interactive Streamlit dashboard supports exploratory analysis. Future: productionize with live HDFS/Spark/MySQL, forecasting, hotspot mapping, station-level drilldowns.', y)

c.save()
print(pdf_path)
