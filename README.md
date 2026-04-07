# 🚗 London ULEZ Expansion: Used Car Market Impact Analysis

This end-to-end Data Engineering and Analytics project investigates the economic effects of the Ultra Low Emission Zone (ULEZ) expansions on the UK used car market. Specifically, it analyzes how the policy affected non-compliant diesel vehicle prices compared to compliant ones.

## 📊 Analytics & Insights


![Dashboard Overview](docs/images/dashboard_overview.png)
*Live market metrics and price gap analysis between compliant and non-compliant vehicles.*

![Diesel Devaluation Analysis](docs/images/diesel_devaluation.png)
*Detailed ranking of top 30 diesel models most affected by the ULEZ expansion.*

![Machine Learning Market Segmentation](docs/images/ml_clusters.png)
*K-Means clustering algorithm segmenting the market based on price, mileage, and explicitly calculating ULEZ Compliance impact.*

![Machine Learning Sample Profiles](docs/images/ml_cluster_samples.png)
*Real vehicles dynamically classified into each cluster directly from the Snowflake data warehouse.*

## 🏗️ Data Engineering Architecture

The project tracks real-world data and implements a robust **Medallion Architecture** on Snowflake using the modern data stack.

```mermaid
flowchart LR
    A[AutoTrader API] -->|Python Ingestion| B(Snowflake: BRONZE)
    B -->|dbt: Clean & Map| C(Snowflake: SILVER)
    C -->|dbt: Data Marts| D(Snowflake: GOLD)
    D -->|Scikit-Learn| F[ML Price Models]
    F -->|Enriched Data| D
    D -->|Python| E[Streamlit Dashboard / API]
    
    style A fill:#f9f9f9,stroke:#333
    style B fill:#CD7F32,color:#fff
    style C fill:#C0C0C0,color:#fff
    style D fill:#FFD700,color:#fff
    style E fill:#ff4b4b,color:#fff
    style F fill:#4CAF50,color:#fff
```

### The Data Pipeline
1. **Bronze Layer (Raw Data):** 
   - A custom Python orchestrator (`scripts/data_engine.py`) extracts near real-time listings from the AutoTrader GraphQL API.
   - Pushes raw attributes to Snowflake using internal stages, allowing continuous ingestion streams.

2. **Silver Layer (Staging & Cleansing):** 
   - Standardizes the data types using **dbt** (`dbt_project/models/staging`).
   - Establishes ULEZ compliance business logic based on vehicle year, emissions, and fuel-type constraints.

3. **Gold Layer (Business Data Marts):** 
   - Aggregates and materializes analysis-ready facts and dimensions via **dbt** (`dbt_project/models/marts`).
   - Serves analytical views (e.g. `mart_diesel_devaluation`) for direct visualization.

4. **Machine Learning:**
   - Evaluates price erosion using regression models based on ULEZ compliance status.

## 🗂️ Project Structure
- `snowflake/`: SQL configurations for roles, warehouses, streams, and tasks.
- `dbt_project/`: Transformation logic (Bronze -> Silver -> Gold).
- `scripts/`: Custom data collectors and the operational data engine.
- `ml_analysis/`: Python-based clustering and price prediction scripts.
- `app/`: Frontend Streamlit application and APIs connecting to Snowflake.

## 🛠️ Technology Stack
- **Data Warehouse:** Snowflake
- **Transformations:** dbt
- **Ingestion Engine:** Python
- **Frontend / API:** Streamlit, FastAPI

## 📝 Core Research Questions
1. Did the ULEZ expansion accelerate the depreciation of non-compliant diesel vehicles?
2. What is the average financial penalty for holding an older diesel car post-2023?
3. How accurately can we predict selling patterns depending on the ULEZ bracket?
