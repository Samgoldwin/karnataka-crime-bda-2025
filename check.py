import sqlite3

con = sqlite3.connect("crime_analytics.db")
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM crime_district_trends")
print(cur.fetchone()[0])
cur.execute("SELECT COUNT(DISTINCT district) FROM crime_district_trends WHERE domain='total_cognizable'")
print(cur.fetchone()[0])
cur.execute("SELECT COUNT(DISTINCT year) FROM crime_district_trends WHERE domain='total_cognizable'")
print(cur.fetchone()[0])
con.close()
