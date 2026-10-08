from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from pathlib import Path
import sqlite3
import textwrap

pdf = Path(__file__).parent / 'Project_Report_Crime_Analytics.pdf'
c = canvas.Canvas(str(pdf), pagesize=A4)
w,h = A4

def title(t,y):
    c.setFont('Helvetica-Bold', 16)
    c.drawString(2*cm, y, t)

def para(text,y, size=10, leading=14):
    c.setFont('Helvetica', size)
    for line in textwrap.wrap(text, 90):
        c.drawString(2*cm, y, line)
        y -= leading
    return y

y = h-2*cm
title('Crime Analytics – Big Data Project Report', y); y-=cm
y = para('Project: Crime in Karnataka 2025 - End-to-End Big Data Pipeline (HDFS/PySpark + MySQL/SQLite + Streamlit)', y)
y = para('Date: 2026-10-08', y)
y -= 5
title('1. Objectives', y); y-=cm
y = para('- Build distributed pipeline: HDFS -> PySpark -> Spark SQL -> MySQL -> Streamlit.', y)
y = para('- Extract/clean NCRB-style district-level crime data (Karnataka 2025).', y)
y = para('- Compute rates, derive KPIs, store aggregated results for fast queries.', y)
y = para('- Create interactive dashboard for analysis.', y)
y -= 5
title('2. Data Sources & Validation', y); y-=cm
y = para('Source: Crime in Karnataka 2025 (Government of Karnataka Police Dept.). Extracted via pdfplumber to 26 CSVs.', y)
y = para('Validation: 1521 trend rows, 39 districts, 3 years (2023–2025). Fact table + 13 normalized tables in DB.', y)
y = para('Cross-checks: district_master_2025, state_trend_2011_2025, head-wise trends consistent.', y)
if y < 4*cm:
    c.showPage(); y=h-2*cm
title('3. Architecture', y); y-=cm
y = para('HDFS(raw/processed) -> PySpark(clean+transform) -> Spark SQL(analytics) -> MySQL/SQLite(aggregates) -> Streamlit(UI).', y)
y = para('Files: scripts/hdfs_upload.sh, scripts/pyspark_crime_analytics.py, scripts/streamlit_app_sqlite.py, schema.sql, requirements.txt.', y)
if y < 4*cm:
    c.showPage(); y=h-2*cm
title('4. Results Summary', y); y-=cm
con = sqlite3.connect('crime_analytics.db')
cur = con.cursor()
cur.execute('SELECT COUNT(*) FROM crime_district_trends'); cnt=cur.fetchone()[0]; y=para(f'Fact rows: {cnt}', y)
cur.execute("SELECT COUNT(DISTINCT district) FROM crime_district_trends WHERE domain='total_cognizable'"); d=cur.fetchone()[0]; y=para(f'Districts: {d}', y)
cur.execute('SELECT MIN(year), MAX(year) FROM crime_district_trends'); a,b=cur.fetchone(); y=para(f'Years: {a}-{b}', y)
con.close()
y -= 5
title('5. Interpretation (Big Data)', y); y-=cm
y = para('Volume: structured dataset (pipeline mirrors distributed architecture). Variety: violent/women/property/missing/recidivism domains. Velocity: batch ETL. Veracity: cleaned/deduped/typed. Value: YoY, district ranking, domain share, recovery rates.', y)
y -= 5
title('6. Data Sources Reference', y); y-=cm
y = para('Primary: Crime in Karnataka 2025 report (Karnataka Police). Extracted tables: district trends, master KPIs, state trend 2011–2025, IPC/SLL heads, violent heads x district, property, missing, recidivism.', y)
y = para('Artifacts: CSVs (26), DB (SQLite), schema (MySQL), Streamlit dashboard, project scripts.', y)

c.save()
print(str(pdf))
