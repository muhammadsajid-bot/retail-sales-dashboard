# Retail Sales Dashboard

A Streamlit-based dashboard for analyzing retail sales performance using uploaded Excel files.

## Features
- Upload retail sales and store master Excel files
- View KPI cards for net sales, target achievement, ATV, return rate, and discount rate
- Explore charts for weekly trend, sales by region, category performance, store leaderboard, and stockout risk
- Filter data by week, region, store, city, store format, and product category
- Review business insights such as best/worst regions and stores missing target
- Download filtered data and insights summary

## Required Files
Upload these two Excel files:
1. Weekly sales file
   - Expected columns include: `store_id`, `week`, `net_sales`, `target_sales`, `transaction_count`, `return_amount`, `discount_amount`, `category`
2. Store master file
   - Expected columns include: `store_id`, `store_name`, `region`, `city`, `store_format`

## Setup
1. Create and activate a virtual environment
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Run Locally
Open the local URL shown by Streamlit, usually:
```text
http://localhost:8501
```

## Notes
- The app can also handle slightly different column names and will fill missing values safely.
- If the app does not detect a column automatically, it will use defaults where possible.
