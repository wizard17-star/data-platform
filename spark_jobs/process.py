from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# 1. Spark Session Configuration
spark = SparkSession.builder \
    .appName("MiniPlatform_StarSchema_Final") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minio") \
    .config("spark.hadoop.fs.s3a.secret.key", "minio12345") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 2. Listen to All Changes from Kafka
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribePattern", "dbserver1.public.*") \
    .option("startingOffsets", "earliest") \
    .load()

# 3. Debezium JSON Schema (full Debezium envelope structure)
debezium_schema = StructType([
    StructField("before", MapType(StringType(), StringType()), True),
    StructField("after", MapType(StringType(), StringType()), True),
    StructField("source", MapType(StringType(), StringType()), True),
    StructField("op", StringType(), True),
    StructField("ts_ms", StringType(), True),
    StructField("transaction", StringType(), True)
])

# 4. Layered Data Processing
def process_batch(df, epoch_id):
    df.persist()
    
    print(f"\n{'='*80}")
    print(f"EPOCH {epoch_id} - Start")
    print(f"{'='*80}")
    
    # --- BRONZE LAYER: Raw Data ---
    try:
        df.write.format("delta").mode("append").save("s3a://lake/bronze/all_events")
        bronze_count = df.count()
        print(f"✅ BRONZE: {bronze_count} messages written")
    except Exception as e:
        print(f"❌ BRONZE error: {e}")
        df.unpersist()
        return

    # Parse JSON
    try:
        parsed_df = df.select(
            col("topic"),
            from_json(col("value").cast("string"), debezium_schema).alias("event")
        )
        parsed_df.persist()
    except Exception as e:
        print(f"❌ JSON parse error: {e}")
        df.unpersist()
        return

    # --- SILVER LAYER: Cleaned Data ---
    try:
        # Customer Silver
        cust_silver = parsed_df.filter(col("topic") == "dbserver1.public.customer") \
            .select(col("event.after").alias("after")) \
            .filter(col("after").isNotNull()) \
            .select(
                col("after")["customerid"].cast("long").alias("customer_id"),
                col("after")["firstname"].alias("first_name"),
                col("after")["lastname"].alias("last_name"),
                col("after")["emailaddress"].alias("email"),
                current_timestamp().alias("processed_at")
            ).filter(col("customer_id").isNotNull())
        
        if not cust_silver.isEmpty():
            cust_silver_count = cust_silver.count()
            cust_silver.write.format("delta").mode("append").save("s3a://lake/silver/customer")
            print(f"✅ SILVER_CUSTOMER: {cust_silver_count} records written")

        # Product Silver
        prod_silver = parsed_df.filter(col("topic") == "dbserver1.public.product") \
            .select(col("event.after").alias("after")) \
            .filter(col("after").isNotNull()) \
            .select(
                col("after")["productid"].cast("long").alias("product_id"),
                col("after")["name"].alias("product_name"),
                col("after")["category"].alias("category"),
                col("after")["price"].cast("double").alias("price"),
                current_timestamp().alias("processed_at")
            ).filter(col("product_id").isNotNull())
        
        if not prod_silver.isEmpty():
            prod_silver_count = prod_silver.count()
            prod_silver.write.format("delta").mode("append").save("s3a://lake/silver/product")
            print(f"✅ SILVER_PRODUCT: {prod_silver_count} records written")

        # SalesOrder Silver
        sales_silver = parsed_df.filter(col("topic") == "dbserver1.public.salesorder") \
            .select(col("event.after").alias("after")) \
            .filter(col("after").isNotNull()) \
            .select(
                col("after")["salesorderid"].cast("long").alias("order_id"),  # ← salesorderid
                col("after")["customerid"].cast("long").alias("customer_id"),
                col("after")["productid"].cast("long").alias("product_id"),
                col("after")["orderqty"].cast("int").alias("quantity"),  # ← orderqty
                col("after")["orderdate"].alias("order_date"),
                current_timestamp().alias("processed_at")
            ).filter(col("order_id").isNotNull())
        
        if not sales_silver.isEmpty():
            sales_silver_count = sales_silver.count()
            sales_silver.write.format("delta").mode("append").save("s3a://lake/silver/salesorder")
            print(f"✅ SILVER_SALESORDER: {sales_silver_count} records written")
            
    except Exception as e:
        print(f"❌ SILVER layer error: {e}")

    # --- GOLD LAYER: DIM_CUSTOMER ---
    try:
        cust_df = parsed_df.filter(col("topic") == "dbserver1.public.customer") \
            .select(col("event.after").alias("after")) \
            .filter(col("after").isNotNull())
        
        cust_df = cust_df.select(
            col("after")["customerid"].cast("long").alias("customerid"),
            col("after")["firstname"].alias("firstname"),
            col("after")["lastname"].alias("lastname"),
            col("after")["emailaddress"].alias("emailaddress")
        ).filter(col("customerid").isNotNull())
        
        if not cust_df.isEmpty():
            cust_count = cust_df.count()
            cust_df.write.format("delta").mode("append").save("s3a://lake/gold/dim_customer")
            print(f"✅ GOLD_DIM_CUSTOMER: {cust_count} records written")
        else:
            print(f"⚠️ GOLD_DIM_CUSTOMER: Empty batch")
    except Exception as e:
        print(f"❌ GOLD_DIM_CUSTOMER error: {e}")

    # --- GOLD LAYER: DIM_PRODUCT ---
    try:
        prod_df = parsed_df.filter(col("topic") == "dbserver1.public.product") \
            .select(col("event.after").alias("after")) \
            .filter(col("after").isNotNull())
        
        prod_df = prod_df.select(
            col("after")["productid"].cast("long").alias("productid"),
            col("after")["name"].alias("name"),
            col("after")["category"].alias("category"),
            col("after")["price"].cast("double").alias("price")
        ).filter(col("productid").isNotNull())
        
        if not prod_df.isEmpty():
            prod_count = prod_df.count()
            prod_df.write.format("delta").mode("append").save("s3a://lake/gold/dim_product")
            print(f"✅ GOLD_DIM_PRODUCT: {prod_count} records written")
        else:
            print(f"⚠️ GOLD_DIM_PRODUCT: Empty batch")
    except Exception as e:
        print(f"❌ GOLD_DIM_PRODUCT error: {e}")

    # --- GOLD LAYER: FACT_SALES ---
    try:
        sales_df = parsed_df.filter(col("topic") == "dbserver1.public.salesorder") \
            .select(col("event.after").alias("after")) \
            .filter(col("after").isNotNull())
        
        sales_df = sales_df.select(
            col("after")["salesorderid"].cast("long").alias("order_id"),  # ← salesorderid
            col("after")["customerid"].cast("long").alias("customer_id"),
            col("after")["productid"].cast("long").alias("product_id"),
            col("after")["orderqty"].cast("int").alias("quantity"),  # ← orderqty
            col("after")["orderdate"].alias("order_date")
        ).filter(col("order_id").isNotNull())
        
        if not sales_df.isEmpty():
            sales_count = sales_df.count()
            sales_df.write.format("delta").mode("append").save("s3a://lake/gold/fact_sales")
            print(f"✅ GOLD_FACT_SALES: {sales_count} records written")
        else:
            print(f"⚠️ GOLD_FACT_SALES: Empty batch")
    except Exception as e:
        print(f"❌ GOLD_FACT_SALES error: {e}")

    parsed_df.unpersist()
    df.unpersist()
    print(f"{'='*80}\n")

# 5. Start Pipeline
query = raw_df.writeStream \
    .foreachBatch(process_batch) \
    .option("checkpointLocation", "s3a://lake/checkpoints/star_schema_final") \
    .start()

query.awaitTermination()