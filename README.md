# Impact of ULEZ Expansion on Used Car Prices in London

This project analyzes the economic effects of the Ultra Low Emission Zone (ULEZ) expansions on the UK used car market using Snowflake (Medallion Architecture), dbt, and Machine Learning.

## Project Structure
- `snowflake/`: SQL setup for Databases, Roles, and Schemas.
- `dbt_project/`: Transformation layers (Bronze, Silver, Gold).
- `ml_analysis/`: Python scripts for Price Prediction and Causal Inference.
- `scripts/`: Data ingestion and orchestration.

## Research Questions
- Did the expansion of London's ULEZ policy affect the price of used vehicles depending on emissions compliance?
- What is the price penalty for non-compliant diesel vehicles after 2023?
- Can we predict car prices accurately based on ULEZ status?
