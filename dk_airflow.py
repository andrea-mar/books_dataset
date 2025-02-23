from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd

def generate_report():
    df = pd.read_csv("inventory_data_with_risk.csv")
    df["Stock Risk"] = df.apply(
        lambda row: "High" if row["Retailer number of units in stock"] + row["Current number of units in DK warehouse"] < row["Forecast sales for next 4 weeks"]
        else "Low",
        axis=1
    )
    df.to_excel("automated_inventory_report.xlsx", index=False)

# Define Airflow DAG
dag = DAG(
    "inventory_report_dag",
    schedule_interval="@daily",
    start_date=datetime(2025, 2, 22),
    catchup=False
)

task = PythonOperator(
    task_id="generate_inventory_report",
    python_callable=generate_report,
    dag=dag
)
