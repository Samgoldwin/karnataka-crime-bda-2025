rem Set MySQL connector jar path if not in SPARK_HOME/jars
set MYSQL_JAR=C:\path\to\mysql-connector-j-8.4.0.jar
spark-submit --jars %%MYSQL_JAR%% scripts\pyspark_crime_analytics.py
