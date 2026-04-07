import time
import os
import snowflake.connector
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def get_snowflake_conn():
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database='ULEZ_DB',
        schema='BRONZE',
        role=os.getenv('SNOWFLAKE_ROLE', 'ULEZ_DEVELOPER')
    )

def ingest_file(file_path):
    """
    Individually ingests a CSV file into its corresponding table.
    """
    brand = Path(file_path).stem.upper()
    table_name = f"{brand}_RAW"
    file_name = Path(file_path).name
    
    conn = get_snowflake_conn()
    cursor = conn.cursor()
    
    try:
        # 1. Ensure table structure exists (generic car listing schema)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                model VARCHAR, year INTEGER, price INTEGER,
                transmission VARCHAR, mileage INTEGER, fuelType VARCHAR,
                tax INTEGER, mpg FLOAT, engineSize FLOAT
            )
        """)
        
        # 2. Stage and Ingest
        print(f"DEBUG: Found {brand} data. Processing...")
        normalized_path = str(Path(file_path).absolute()).replace("\\", "/")
        cursor.execute("CREATE STAGE IF NOT EXISTS ingest_stage")
        cursor.execute(f"PUT file://{normalized_path} @ingest_stage AUTO_COMPRESS=TRUE")
        
        cursor.execute(f"""
            COPY INTO {table_name} 
            FROM @ingest_stage/{file_name}.gz
            FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1)
            ON_ERROR = 'CONTINUE'
        """)
        print(f"OK: {brand} loaded into Snowflake.")
        
    finally:
        cursor.close()
        conn.close()

class DataIngestHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".csv"):
            ingest_file(event.src_path)

from autotrader_collector import fetch_autotrader_listings

def ingest_autotrader(make="BMW", fuel_type="Petrol", pages=1):
    """
    Fetches and ingests AutoTrader listings directly into Snowflake.
    """
    all_listings = []
    for p in range(1, pages + 1):
        listings = fetch_autotrader_listings(make=make, fuel_type_filter=fuel_type, pages=p)
        if listings:
            all_listings.extend(listings)
    
    if not all_listings:
        return

    conn = get_snowflake_conn()
    cursor = conn.cursor()
    
    try:
        print(f"DB: Loading {len(all_listings)} {make} ({fuel_type}) records...")
        for car in all_listings:
            clean_price = str(car.get('price', 0)).replace('£', '').replace(',', '')
            
            cursor.execute(f"""
                INSERT INTO BRONZE.AUTOTRADER_RAW 
                (id, brand, title, price, year, mileage, fuelType, engineSize, transmission)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                car.get('id'), make, car.get('title'), clean_price, 
                car.get('year'), car.get('mileage'), car.get('fuelType'), 
                car.get('engineSize'), car.get('transmission')
            ))
        print(f"OK: {make} {fuel_type} updated ({len(all_listings)} records).")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("START: ULEZ Live Data Engine Started...")
    print("INFO: Mode: Conservative Ingestion (Speed Optimized)")
    
    # Reduced list to keep execution time short
    brands = ['BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen']
    for brand in brands:
        for fuel in ['Petrol', 'Diesel']:
            ingest_autotrader(make=brand, fuel_type=fuel, pages=2)
    
    print("\nDONE: Full update complete. Dashboard is now updated with real data.")
