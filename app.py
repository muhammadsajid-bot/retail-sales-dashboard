import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Retail Sales Intelligence", layout="wide")
st.title("📊 Retail Sales Intelligence Dashboard")
st.markdown("##")

# --- CUSTOM CSS FOR METRICS ---
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 24px;
}
</style>
""", unsafe_allow_html=True)

# --- FILE UPLOADERS ---
st.sidebar.header("1. Data Input")
sales_file = st.sidebar.file_uploader("Upload Weekly Sales (xlsx)", type=["xlsx"])
master_file = st.sidebar.file_uploader("Upload Store Master (xlsx)", type=["xlsx"])

# --- DATA PROCESSING FUNCTION ---
def normalize_column_name(col):
    return str(col).strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def sanitize_numeric_columns(df):
    df = df.copy()
    numeric_like_names = {
        "net_sales", "gross_sales", "sales", "target_sales", "sales_target", "return_amount", "returns_amount",
        "discount_amount", "transactions", "transaction_count", "stockout_event", "stockout_events",
        "inventory_level", "inventory_on_hand", "units_sold", "footfall", "marketing_spend", "customer_rating"
    }

    for col in df.columns:
        col_name = normalize_column_name(col)
        if col_name in numeric_like_names or "sales" in col_name or "amount" in col_name or "count" in col_name or "rate" in col_name or "level" in col_name or "score" in col_name:
            cleaned = df[col].astype(str).str.strip()
            cleaned = cleaned.replace({r"^$": pd.NA, "not_available": pd.NA, "na": pd.NA, "n/a": pd.NA, "none": pd.NA, "null": pd.NA, "nan": pd.NA}, regex=True)
            cleaned = cleaned.str.replace(r"[$,]", "", regex=True)
            numeric_series = pd.to_numeric(cleaned, errors="coerce")
            if numeric_series.notna().sum() > 0:
                df[col] = numeric_series.fillna(0)
            else:
                df[col] = cleaned
    return df


def normalize_columns(df):
    df = df.copy()
    df.columns = [normalize_column_name(col) for col in df.columns]
    return df


def resolve_column(df, candidates):
    normalized_columns = {normalize_column_name(col): col for col in df.columns}
    for candidate in candidates:
        if normalize_column_name(candidate) in normalized_columns:
            return normalized_columns[normalize_column_name(candidate)]
    return None


def infer_week_column(sales_df):
    week_candidates = [
        "week", "week_no", "week_number", "sales_week", "wk", "period", "report_week",
        "week_label", "week_start", "week_start_date", "week_end", "date", "transaction_date", "sales_date"
    ]
    week_col = resolve_column(sales_df, week_candidates)
    if week_col:
        return week_col

    for col in sales_df.columns:
        if normalize_column_name(col) in {"date", "transaction_date", "sales_date", "week_start", "week_start_date", "week_end"}:
            return col
    return None


@st.cache_data
def load_and_merge_data(sales_df, master_df):
    sales_df = normalize_columns(sales_df)
    master_df = normalize_columns(master_df)

    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["store_id", "storeid", "store"]): "store_id"}) if resolve_column(sales_df, ["store_id", "storeid", "store"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["week_start_date", "week_start", "week_date", "date", "transaction_date", "sales_date", "week", "week_no", "week_number", "sales_week", "wk", "period"]): "week"}) if resolve_column(sales_df, ["week_start_date", "week_start", "week_date", "date", "transaction_date", "sales_date", "week", "week_no", "week_number", "sales_week", "wk", "period"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["net_sales", "sales", "net"]): "net_sales"}) if resolve_column(sales_df, ["net_sales", "sales", "net"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["sales_target", "target_sales", "sales_target_amount", "target"]): "target_sales"}) if resolve_column(sales_df, ["sales_target", "target_sales", "sales_target_amount", "target"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["transaction_count", "transactions", "txn_count", "transaction"]): "transaction_count"}) if resolve_column(sales_df, ["transaction_count", "transactions", "txn_count", "transaction"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["return_amount", "returns", "return_amt", "returns_amount"]): "return_amount"}) if resolve_column(sales_df, ["return_amount", "returns", "return_amt", "returns_amount"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["discount_amount", "discounts", "discount_amt"]): "discount_amount"}) if resolve_column(sales_df, ["discount_amount", "discounts", "discount_amt"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["category", "product_category", "prod_category", "product"]): "category"}) if resolve_column(sales_df, ["category", "product_category", "prod_category", "product"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["stockout_event", "stockout", "stockout_flag", "stockout_flagged", "stockouts"]): "stockout_event"}) if resolve_column(sales_df, ["stockout_event", "stockout", "stockout_flag", "stockout_flagged", "stockouts"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["store_name", "store", "name"]): "store_name"}) if resolve_column(sales_df, ["store_name", "store", "name"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["region", "sales_region"]): "region"}) if resolve_column(sales_df, ["region", "sales_region"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["city", "location"]): "city"}) if resolve_column(sales_df, ["city", "location"]) else sales_df
    sales_df = sales_df.rename(columns={resolve_column(sales_df, ["store_format", "format", "storetype"]): "store_format"}) if resolve_column(sales_df, ["store_format", "format", "storetype"]) else sales_df

    master_df = master_df.rename(columns={resolve_column(master_df, ["store_id", "storeid", "store"]): "store_id"}) if resolve_column(master_df, ["store_id", "storeid", "store"]) else master_df
    master_df = master_df.rename(columns={resolve_column(master_df, ["store_name", "store", "name"]): "store_name"}) if resolve_column(master_df, ["store_name", "store", "name"]) else master_df
    master_df = master_df.rename(columns={resolve_column(master_df, ["region", "sales_region"]): "region"}) if resolve_column(master_df, ["region", "sales_region"]) else master_df
    master_df = master_df.rename(columns={resolve_column(master_df, ["store_format", "format", "storetype"]): "store_format"}) if resolve_column(master_df, ["store_format", "format", "storetype"]) else master_df
    master_df = master_df.rename(columns={resolve_column(master_df, ["city", "location"]): "city"}) if resolve_column(master_df, ["city", "location"]) else master_df

    if "week" not in sales_df.columns:
        week_col = infer_week_column(sales_df)
        if week_col:
            sales_df["week"] = sales_df[week_col]
        else:
            sales_df["week"] = [f"Week {i + 1}" for i in range(len(sales_df))]

    if "stockout_event" not in sales_df.columns:
        sales_df["stockout_event"] = 0

    for col in ["net_sales", "target_sales", "return_amount", "discount_amount", "transaction_count", "stockout_event"]:
        if col in sales_df.columns:
            sales_df[col] = pd.to_numeric(sales_df[col], errors="coerce").fillna(0)

    if "week" in sales_df.columns:
        sales_df["week"] = pd.to_datetime(sales_df["week"], errors="coerce")
        sales_df["week"] = sales_df["week"].dt.strftime("%Y-%m-%d")
        sales_df["week"] = sales_df["week"].fillna("Unknown")

    required_sales_columns = ["store_id", "week", "net_sales"]
    missing_sales_columns = [col for col in required_sales_columns if col not in sales_df.columns]
    if missing_sales_columns:
        available_columns = ", ".join(sales_df.columns.tolist()) if len(sales_df.columns) else "none"
        raise ValueError(f"Sales file is missing required columns: {', '.join(missing_sales_columns)}. Available columns: {available_columns}")

    if "store_id" not in master_df.columns:
        raise ValueError("Store master file is missing required column: store_id")

    master_lookup = master_df[["store_id", "store_name", "region", "city", "store_format"]].copy()
    master_lookup = master_lookup.rename(columns={
        "store_name": "master_store_name",
        "region": "master_region",
        "city": "master_city",
        "store_format": "master_store_format"
    })
    df = pd.merge(sales_df, master_lookup, on="store_id", how="left")
    df = sanitize_numeric_columns(df)

    for col, master_col in {
        "store_name": "master_store_name",
        "region": "master_region",
        "city": "master_city",
        "store_format": "master_store_format",
    }.items():
        if col in df.columns:
            df[col] = df[col].fillna(df[master_col])
        elif master_col in df.columns:
            df[col] = df[master_col]

    for col, default in {
        "store_name": df["store_id"].astype(str),
        "region": "Unknown",
        "city": "Unknown",
        "store_format": "Unknown",
        "category": "Unknown",
        "target_sales": 0,
        "return_amount": 0,
        "discount_amount": 0,
        "transaction_count": 0,
        "stockout_event": 0,
    }.items():
        if col not in df.columns:
            df[col] = default

    df["store_name"] = df["store_name"].fillna("Unknown").astype(str)
    df["region"] = df["region"].fillna("Unknown").astype(str)
    df["city"] = df["city"].fillna("Unknown").astype(str)
    df["store_format"] = df["store_format"].fillna("Unknown").astype(str)
    df["category"] = df["category"].fillna("Unknown").astype(str)
    df["week"] = df["week"].fillna("Unknown").astype(str)

    return df

# --- MAIN APP LOGIC ---
if sales_file and master_file:
    try:
        df_sales = pd.read_excel(sales_file)
        df_master = pd.read_excel(master_file)
        df = load_and_merge_data(df_sales, df_master)

        if "city" not in df.columns:
            df["city"] = "Unknown"
        df["week"] = df["week"].fillna("Unknown").astype(str)
        df["region"] = df["region"].fillna("Unknown").astype(str)
        df["store_name"] = df["store_name"].fillna("Unknown").astype(str)
        df["city"] = df["city"].fillna("Unknown").astype(str)
        df["store_format"] = df["store_format"].fillna("Unknown").astype(str)
        df["category"] = df["category"].fillna("Unknown").astype(str)

        st.sidebar.header("2. Filter Intelligence")
        week_options = sorted(df["week"].dropna().unique().tolist())
        region_options = sorted(df["region"].dropna().unique().tolist())
        store_options = sorted(df["store_name"].dropna().unique().tolist())
        city_options = sorted(df["city"].dropna().unique().tolist())
        store_format_options = sorted(df["store_format"].dropna().unique().tolist())
        category_options = sorted(df["category"].dropna().unique().tolist())

        selected_weeks = st.sidebar.multiselect("Select Week:", options=week_options, default=week_options)
        selected_regions = st.sidebar.multiselect("Select Region:", options=region_options, default=region_options)
        selected_stores = st.sidebar.multiselect("Select Store:", options=store_options, default=store_options)
        selected_cities = st.sidebar.multiselect("Select City:", options=city_options, default=city_options)
        selected_formats = st.sidebar.multiselect("Store Format:", options=store_format_options, default=store_format_options)
        selected_categories = st.sidebar.multiselect("Product Category:", options=category_options, default=category_options)

        mask = pd.Series(True, index=df.index)
        if selected_weeks:
            mask &= df["week"].isin(selected_weeks)
        if selected_regions:
            mask &= df["region"].isin(selected_regions)
        if selected_stores:
            mask &= df["store_name"].isin(selected_stores)
        if selected_cities:
            mask &= df["city"].isin(selected_cities)
        if selected_formats:
            mask &= df["store_format"].isin(selected_formats)
        if selected_categories:
            mask &= df["category"].isin(selected_categories)

        df_selection = df.loc[mask].copy()
        if df_selection.empty:
            st.warning("No data matches the selected filters.")
            st.stop()

        total_net_sales = df_selection["net_sales"].sum()
        total_target = df_selection["target_sales"].sum()
        total_returns = df_selection["return_amount"].sum()
        total_discounts = df_selection["discount_amount"].sum()
        total_txns = df_selection["transaction_count"].sum()

        target_achievement = (total_net_sales / total_target) * 100 if total_target != 0 else 0
        atv = total_net_sales / total_txns if total_txns != 0 else 0
        return_rate = (total_returns / total_net_sales) * 100 if total_net_sales != 0 else 0
        discount_rate = (total_discounts / (total_net_sales + total_discounts)) * 100 if (total_net_sales + total_discounts) != 0 else 0

        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric(label="Net Sales", value=f"${total_net_sales:,.0f}")
        kpi2.metric(label="Target Achievement", value=f"{target_achievement:.1f}%")
        kpi3.metric(label="Avg Transaction (ATV)", value=f"${atv:.2f}")
        kpi4.metric(label="Return Rate", value=f"{return_rate:.1f}%")
        kpi5.metric(label="Discount Rate", value=f"{discount_rate:.1f}%")

        st.markdown("---")

        st.subheader("Business Insight Summary")
        insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)

        region_perf = df_selection.groupby("region")["net_sales"].sum().sort_values(ascending=False)
        best_region = region_perf.index[0] if not region_perf.empty else "N/A"
        worst_region = region_perf.index[-1] if not region_perf.empty else "N/A"

        store_target_gap = df_selection.groupby("store_name").agg(
            net_sales=("net_sales", "sum"),
            target_sales=("target_sales", "sum")
        )
        stores_missing_target = store_target_gap[store_target_gap["net_sales"] < store_target_gap["target_sales"]].sort_values("net_sales")

        return_category = df_selection.groupby("category").agg(
            net_sales=("net_sales", "sum"),
            return_amount=("return_amount", "sum")
        )
        return_category["return_rate"] = (return_category["return_amount"] / return_category["net_sales"] * 100).replace([float("inf"), float("-inf")], 0)
        high_return_category = return_category.sort_values("return_rate", ascending=False).index[0] if not return_category.empty else "N/A"

        insight_col1.metric("Best Region", best_region)
        insight_col2.metric("Worst Region", worst_region)
        insight_col3.metric("Stores Missing Target", f"{len(stores_missing_target)}")
        insight_col4.metric("High Return Category", high_return_category)

        with st.expander("Detailed Insights"):
            st.write(f"- Best-performing region: {best_region}")
            st.write(f"- Lowest-performing region: {worst_region}")
            if not stores_missing_target.empty:
                st.write("- Stores below target:")
                st.dataframe(stores_missing_target.head(10).reset_index())
            else:
                st.write("- No stores are below target in the current selection.")
            st.write(f"- Category with the highest return rate: {high_return_category}")

        st.markdown("---")

        col_left, col_right = st.columns(2)
        sales_trend = df_selection.groupby("week")["net_sales"].sum().reset_index()
        fig_trend = px.line(sales_trend, x="week", y="net_sales", title="<b>Weekly Sales Trend</b>", markers=True, template="plotly_white")
        col_left.plotly_chart(fig_trend, width="stretch")

        sales_region = df_selection.groupby("region")["net_sales"].sum().reset_index()
        fig_region = px.pie(sales_region, values="net_sales", names="region", title="<b>Sales by Region</b>", hole=0.4)
        col_right.plotly_chart(fig_region, width="stretch")

        col_mid1, col_mid2 = st.columns(2)
        cat_perf = df_selection.groupby("category")["net_sales"].sum().sort_values(ascending=True).reset_index()
        fig_cat = px.bar(cat_perf, x="net_sales", y="category", orientation="h", title="<b>Category Performance</b>", color_discrete_sequence=["#0083B8"])
        col_mid1.plotly_chart(fig_cat, width="stretch")

        store_perf = df_selection.groupby("store_name")["net_sales"].sum().sort_values(ascending=False).head(10).reset_index()
        fig_store = px.bar(store_perf, x="store_name", y="net_sales", title="<b>Top 10 Stores Leaderboard</b>", color="net_sales")
        col_mid2.plotly_chart(fig_store, width="stretch")

        st.markdown("### Stockout Risk Analysis")
        if "stockout_event" in df_selection.columns:
            stockout_df = df_selection.groupby("store_name")["stockout_event"].sum().sort_values(ascending=False).head(10).reset_index()
            fig_stock = px.bar(stockout_df, x="store_name", y="stockout_event", title="<b>Stores with Highest Stockout Risk (Count)</b>", color_discrete_sequence=["#FF4B4B"])
            st.plotly_chart(fig_stock, width="stretch")
        else:
            st.info("Stockout event data column not detected. Ensure 'stockout_event' is in your sales file.")

        st.markdown("---")
        st.subheader("Raw Filtered Data")
        csv = df_selection.to_csv(index=False).encode("utf-8")
        summary_text = (
            f"Retail Sales Summary\n"
            f"Net Sales: ${total_net_sales:,.0f}\n"
            f"Target Achievement: {target_achievement:.1f}%\n"
            f"Return Rate: {return_rate:.1f}%\n"
            f"Discount Rate: {discount_rate:.1f}%\n"
            f"Best Region: {best_region}\n"
            f"Worst Region: {worst_region}\n"
            f"Stores Missing Target: {len(stores_missing_target)}\n"
            f"High Return Category: {high_return_category}\n"
        )
        col_export1, col_export2 = st.columns(2)
        col_export1.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name="filtered_retail_data.csv",
            mime="text/csv",
        )
        col_export2.download_button(
            label="Download Insights Summary",
            data=summary_text,
            file_name="retail_insights_summary.txt",
            mime="text/plain",
        )
        st.dataframe(sanitize_numeric_columns(df_selection))

        st.caption("Share this app by deploying it to Streamlit Community Cloud or sharing the local URL once it is running with streamlit run app.py")

    except Exception as e:
        st.error(f"Error processing data: {e}")
        st.info("Ensure both Excel files have matching 'store_id' columns and the expected numeric fields.")

else:
    st.info("Please upload both 'Weekly Sales' and 'Store Master' Excel files to begin.")

# --- HELP SECTION ---
with st.expander("Required Data Schema"):
    st.write("""
    **retail_weekly_sales.xlsx**:
    - `store_id`, `week`, `net_sales`, `target_sales`, `transaction_count`, `return_amount`, `discount_amount`, `category`, `stockout_event`

    **store_master.xlsx**:
    - `store_id`, `store_name`, `region`, `city`, `store_format`
    """)