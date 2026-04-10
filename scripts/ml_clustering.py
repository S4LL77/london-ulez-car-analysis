import logging
import os

import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from snowflake.connector import connect
from snowflake.connector.pandas_tools import write_pandas

# Enterprise Logging Configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ML_ClusteringPipeline")


def init_snowflake_connection():
    load_dotenv()
    return connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="GOLD",  # Writing to Gold
        role=os.getenv("SNOWFLAKE_ROLE"),
    )


def extract_features(conn) -> pd.DataFrame:
    """Extract raw operational data from the Silver layer."""
    logger.info("Extracting data from SILVER.FCT_CARS...")
    query = """
        SELECT 
            brand, 
            model, 
            year, 
            price, 
            mileage,
            fuel_type,
            engine_size,
            is_ulez_compliant
        FROM SILVER.FCT_CARS
        WHERE price IS NOT NULL 
          AND mileage IS NOT NULL
          AND year IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    # Ensure column names are uppercase for Snowflake compatibility
    df.columns = [c.upper() for c in df.columns]
    logger.info(f"Extracted {len(df)} records for training.")
    return df


def train_and_predict(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    """Train K-Means model and predict clusters."""
    logger.info("Initializing Feature Engineering and Model Training...")

    # Select features for clustering
    features = ["PRICE", "MILEAGE", "YEAR"]
    X = df[features].copy()

    # 1. Scale Features (Standardization is critical for K-Means)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 2. Train Model
    logger.info(f"Training K-Means with K={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["CLUSTER_ID"] = kmeans.fit_predict(X_scaled)

    # 3. Profiling / Naming Clusters based on Business Logic
    # We aggregate the means of each cluster to dynamically name them
    cluster_means = df.groupby("CLUSTER_ID")[features].mean()

    # Basic logic: Sort by price to identify "Premium" vs "Value"
    sorted_by_price = cluster_means.sort_values(by="PRICE")
    value_cluster_id = sorted_by_price.index[0]
    mid_cluster_id = sorted_by_price.index[1]
    premium_cluster_id = sorted_by_price.index[2]

    def map_cluster_name(row):
        is_compliant = row["IS_ULEZ_COMPLIANT"]
        cid = row["CLUSTER_ID"]

        if cid == premium_cluster_id:
            return (
                "Premium Segment (ULEZ Compliant)"
                if is_compliant
                else "Premium Segment (Non-Compliant)"
            )
        elif cid == mid_cluster_id:
            return (
                "Standard Market (ULEZ Compliant)"
                if is_compliant
                else "Standard Market (Non-Compliant)"
            )
        elif cid == value_cluster_id:
            return (
                "Budget Entry (ULEZ Compliant)"
                if is_compliant
                else "Desperate Dump (Non-Compliant)"
            )

    df["CLUSTER_NAME"] = df.apply(map_cluster_name, axis=1)
    logger.info("Clustering completed and business profiles assigned.")
    return df


def load_to_snowflake(df: pd.DataFrame, conn):
    """Load results into the GOLD layer."""
    table_name = "MART_MARKET_CLUSTERS"
    logger.info(f"Writing {len(df)} records to GOLD.{table_name}...")

    # In an enterprise setting, we usually truncate/load or use MERGE for ML features
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            BRAND VARCHAR,
            MODEL VARCHAR,
            YEAR NUMBER,
            PRICE FLOAT,
            MILEAGE FLOAT,
            FUEL_TYPE VARCHAR,
            ENGINE_SIZE FLOAT,
            IS_ULEZ_COMPLIANT BOOLEAN,
            CLUSTER_ID NUMBER,
            CLUSTER_NAME VARCHAR
        )
    """)
    cursor.execute(f"TRUNCATE TABLE {table_name}")

    success, nchunks, nrows, _ = write_pandas(conn, df, table_name)
    logger.info(f"Successfully loaded {nrows} rows into {table_name}.")


def run_pipeline():
    logger.info("--- Starting ML Pipeline ---")
    try:
        conn = init_snowflake_connection()
        df_raw = extract_features(conn)

        if df_raw.empty:
            logger.warning("No data extracted. Aborting pipeline.")
            return

        df_scored = train_and_predict(df_raw, n_clusters=3)
        load_to_snowflake(df_scored, conn)

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise
    finally:
        if "conn" in locals():
            conn.close()
            logger.info("Snowflake connection closed.")
    logger.info("--- Pipeline Execution Finished ---")


if __name__ == "__main__":
    run_pipeline()
