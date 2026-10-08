from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim

MYSQL_URL = "jdbc:mysql://localhost:3306/crime_analytics?useSSL=false&serverTimezone=Asia/Kolkata"
MYSQL_USER = "root"
MYSQL_PWD = "YOUR_PASSWORD"
MYSQL_DRIVER = "com.mysql.cj.jdbc.Driver"

spark = SparkSession.builder \
    .appName("CrimeAnalytics_Karnataka2025") \
    .getOrCreate()

def write_jdbc(df, table, mode="overwrite"):
    df.write \
        .format("jdbc") \
        .option("url", MYSQL_URL) \
        .option("dbtable", table) \
        .option("user", MYSQL_USER) \
        .option("password", MYSQL_PWD) \
        .option("driver", MYSQL_DRIVER) \
        .mode(mode) \
        .save()

# 1) master_district_trends_long (fact)
df_long = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/master_district_trends_long.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("district", trim(col("district"))) \
 .withColumn("domain", trim(col("domain"))) \
 .withColumn("table_id", trim(col("table_id"))) \
 .dropDuplicates(["domain","table_id","district","year"])

df_long_clean = df_long.na.fill({
    "cases": 0,
    "population_lakhs_2025": 0.0,
    "rate_2025": 0.0,
    "chargesheeting_rate_2025": 0.0
}).select(
    col("domain"),
    col("table_id"),
    col("district"),
    col("year"),
    col("cases").cast("int"),
    col("population_lakhs_2025").cast("decimal(10,3)").alias("population_lakhs"),
    col("rate_2025").cast("decimal(10,3)").alias("crime_rate"),
    col("chargesheeting_rate_2025").cast("decimal(10,3)").alias("chargesheeting_rate")
)

write_jdbc(df_long_clean, "crime_district_trends", mode="overwrite")

# 2) district_master_2025
df_m25 = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/district_master_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("district", trim(col("district"))).dropDuplicates(["district"])
write_jdbc(df_m25, "district_master_2025", mode="overwrite")

# 3) state_trend_2011_2025
df_st = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/state_trend_2011_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
)
write_jdbc(df_st, "state_trend_2011_2025", mode="overwrite")

# 4) IPC/SLL heads
df_ipc = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/ipc_crime_heads_trend.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("crime_head", trim(col("crime_head"))).dropDuplicates(["crime_head"])
write_jdbc(df_ipc, "ipc_crime_heads_trend", mode="overwrite")

df_sll = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/sll_crime_heads_trend.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("crime_head", trim(col("crime_head"))).dropDuplicates(["crime_head"])
write_jdbc(df_sll, "sll_crime_heads_trend", mode="overwrite")

# 5) violent heads by district
df_v = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/violent_crime_heads_by_district_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("district", trim(col("district"))).dropDuplicates(["district"])
write_jdbc(df_v, "violent_crime_heads_by_district_2025", mode="overwrite")

# 6) property
df_prop_d = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/property_stolen_recovered_district_2023_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("district", trim(col("district")))
write_jdbc(df_prop_d, "property_stolen_recovered_district_2023_2025", mode="overwrite")

df_prop_n = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/property_by_nature_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("nature_of_property", trim(col("nature_of_property")))
write_jdbc(df_prop_n, "property_by_nature_2025", mode="overwrite")

# 7) missing
df_mc = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/missing_children_district_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("district", trim(col("district")))
write_jdbc(df_mc, "missing_children_district_2025", mode="overwrite")

df_mp = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/missing_persons_district_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("district", trim(col("district")))
write_jdbc(df_mp, "missing_persons_district_2025", mode="overwrite")

# 8) recidivism
df_ripc = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/recidivism_ipc_district_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("district", trim(col("district")))
write_jdbc(df_ripc, "recidivism_ipc_district_2025", mode="overwrite")

df_rsll = spark.read.csv(
    "hdfs://localhost:9000/crime/raw/recidivism_sll_district_2025.csv",
    header=True, inferSchema=True, encoding="utf-8-sig"
).withColumn("district", trim(col("district")))
write_jdbc(df_rsll, "recidivism_sll_district_2025", mode="overwrite")

df_long_clean.createOrReplaceTempView("crime_district_trends")
spark.sql("""
  SELECT domain, year, SUM(cases) AS total_cases
  FROM crime_district_trends
  WHERE year IN (2023,2024,2025)
  GROUP BY domain, year
  ORDER BY domain, year
""").show(10, truncate=False)

spark.stop()
