# ==============================================================================
# Course: DS 405 - Big Data Analysis
# Project: Banking Transactions Intelligence System
# Author: David Hany
# ==============================================================================

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, sum, count, lag, rank, desc
from pyspark.sql.window import Window

# 1. إعداد Spark Session
spark = SparkSession.builder \
    .appName("Banking_Transactions_Intelligence") \
    .config("spark.sql.shuffle.partitions", "50") \
    .getOrCreate()

# ==============================================================================
# 2. Data Loading (قراءة الجداول)
# ==============================================================================
print("Loading datasets...")
df_customers = spark.read.csv("customers.csv", header=True, inferSchema=True)
df_accounts = spark.read.csv("accounts.csv", header=True, inferSchema=True)
df_transactions = spark.read.csv("transactions.csv", header=True, inferSchema=True)

# ==============================================================================
# 3. Data Cleaning (تنظيف البيانات)
# Requirements: Clean invalid transactions
# ==============================================================================
# استبعاد القيم الفارغة والمبالغ السالبة غير المنطقية
df_clean_txns = df_transactions.filter((col("amount").isNotNull()) & (col("amount") > 0))

# ==============================================================================
# 4. Feature Engineering & Joins
# Requirements: transaction type classification
# ==============================================================================
# تصنيف المعاملات بناءً على حجمها ونوعها
df_featured = df_clean_txns.withColumn(
    "txn_risk_classification",
    when(col("amount") >= 10000, "High Value / Review Required")
    .when((col("amount") >= 2000) & (col("amount") < 10000), "Medium Value")
    .otherwise("Standard")
)

# ربط الجداول ببعضها للحصول على بيانات متكاملة
df_joined = df_featured.join(df_accounts, "account_id", "left") \
                       .join(df_customers, "customer_id", "left")

# ==============================================================================
# 5. Aggregations & Window Functions
# Requirements: total spend per customer, rank customers by activity, detect sudden spikes (lag)
# ==============================================================================

# أ. إجمالي الصرف لكل عميل
df_total_spend = df_joined.groupBy("customer_id", "customer_name") \
                          .agg(sum("amount").alias("total_spend"))

# ب. ترتيب العملاء حسب نشاطهم (Rank customers by activity)
window_activity = Window.orderBy(desc("total_txns"))
df_customer_rank = df_joined.groupBy("customer_id", "customer_name") \
                            .agg(count("txn_id").alias("total_txns")) \
                            .withColumn("activity_rank", rank().over(window_activity))

# ج. اكتشاف القفزات المفاجئة باستخدام (Lag)
window_lag = Window.partitionBy("account_id").orderBy("timestamp")
df_spikes = df_joined.withColumn("prev_amount", lag("amount", 1).over(window_lag)) \
                     .withColumn("spike_amount_diff", col("amount") - col("prev_amount"))

# ==============================================================================
# 6. SQL Queries for Fraud-like Patterns
# Requirements: SQL queries for fraud-like patterns
# ==============================================================================
# تحويل الـ DataFrame إلى View مؤقت لاستخدام SQL
df_spikes.createOrReplaceTempView("banking_data_view")

# اكتشاف نمط احتيال: معاملة جديدة أكبر بـ 4 أضعاف من المعاملة السابقة لنفس الحساب
# وتصنيفها "High Value"
fraud_query = """
    SELECT 
        customer_name, 
        account_id, 
        txn_id, 
        amount, 
        prev_amount, 
        timestamp,
        txn_type
    FROM banking_data_view
    WHERE prev_amount IS NOT NULL 
      AND amount > (prev_amount * 4)
      AND amount >= 5000
"""
df_fraud_alerts = spark.sql(fraud_query)

print("--- Top 5 Fraud-like Patterns Detected ---")
df_fraud_alerts.show(5)

# ==============================================================================
# 7. Saving Results (Pandas Workaround for Windows)
# ==============================================================================
print("Converting Spark DataFrame to Pandas for saving (Bypassing Windows Hadoop Error)...")

# تحويل نتيجة Spark إلى Pandas
df_final_pandas = df_joined.toPandas()

# إنشاء فولدر الحفظ لو مش موجود
output_dir = "final_submission_data"
os.makedirs(output_dir, exist_ok=True)

# حفظ البيانات كملف CSV
save_path = f"{output_dir}/processed_transactions.csv"
df_final_pandas.to_csv(save_path, index=False)

print(f"Project processing completed successfully! Data saved to: {save_path}")