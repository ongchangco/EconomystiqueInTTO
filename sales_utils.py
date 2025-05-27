import sqlite3
import os
import pandas as pd

def fetch_sales_data():
    # Define paths to the databases
    db_path_2024 = os.path.join("db", "sales_2024.db")
    db_path_2025 = os.path.join("db", "sales_2025.db")

    # Define the fixed order of months
    fixed_order = [
        "apr_2024", "may_2024", "jun_2024", "jul_2024", "aug_2024", "sep_2024", 
        "oct_2024", "nov_2024", "dec_2024", "jan_2025", "feb_2025", "mar_2025", "this_month"
    ]
    
    # Prepare a dictionary to hold the sales data for each month
    sales_data = {month: 0 for month in fixed_order}  # Initialize with zero sales

    # Connect to the sales_2024.db for months April to December
    conn_2024 = sqlite3.connect(db_path_2024)
    cursor_2024 = conn_2024.cursor()

    # Fetch sales data for months April to December from sales_2024.db
    for month in ["apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]:
        cursor_2024.execute(f"SELECT SUM(price * quantity_sold) FROM {month}")
        total_sales = cursor_2024.fetchone()
        sales_data[f"{month}_2024"] = total_sales[0] if total_sales and total_sales[0] is not None else 0

    conn_2024.close()

    # Connect to the sales_2025.db for months January to March and April
    conn_2025 = sqlite3.connect(db_path_2025)
    cursor_2025 = conn_2025.cursor()

    # Fetch sales data for months January to March from sales_2025.db
    for month in ["jan", "feb", "mar"]:
        cursor_2025.execute(f"SELECT SUM(price * quantity_sold) FROM {month}")
        total_sales = cursor_2025.fetchone()
        sales_data[f"{month}_2025"] = total_sales[0] if total_sales and total_sales[0] is not None else 0

    # Fetch sales data for April from sales_2025.db (this will not overwrite data from 2024)
    cursor_2025.execute(f"SELECT SUM(price * quantity_sold) FROM apr")
    total_sales = cursor_2025.fetchone()
    sales_data["this_month"] = total_sales[0] if total_sales and total_sales[0] is not None else 0

    conn_2025.close()

    # Convert to Pandas DataFrame
    df = pd.DataFrame(list(sales_data.items()), columns=["Month", "TotalSales"])

    return df

