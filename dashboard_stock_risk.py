import streamlit as st 
import pandas as pd
import numpy as np

import plotly.express as px
import hvplot.pandas  # Enables interactive hvPlot
import streamlit.components.v1 as components

from bokeh.plotting import figure, save
from bokeh.io import output_file


def use_file_for_bokeh(chart: figure, chart_height=500):
    output_file('bokeh_graph.html')
    save(chart)
    with open("bokeh_graph.html", 'r', encoding='utf-8') as f:
        html = f.read()
    components.html(html, height=chart_height)


def main():
     # Increase Streamlit container width to fit the plot properly
    st.set_page_config(layout="wide")  # Ensures Streamlit uses full page width
    st.title("Stock vs Forecast Comparison")

    # # Load the dataset
    # @st.cache_data
    # def load_data():
    #     return pd.read_excel('data/2025 Feb Data for recruitment task (1).xlsx')

    # st.bokeh_chart = use_file_for_bokeh
    # df = load_data()


    # # Sidebar - User selects stock column
    # st.sidebar.header("Stock vs Forecast Comparison")
    # stock_option = st.sidebar.selectbox(
    #     "Select stock column to compare with forecast sales:",
    #     ["Retailer number of units in stock", 
    #     "Current number of units in DK warehouse", 
    #     "Retailer number of units in stock + Current number of units in DK warehouse"]
    # )

    # # Compute selected stock column
    # if stock_option == "Retailer number of units in stock + Current number of units in DK warehouse":
    #     df["Selected Stock"] = df["Retailer number of units in stock"] + df["Current number of units in DK warehouse"]
    # else:
    #     df["Selected Stock"] = df[stock_option]

    
    # # compute risk model
    # # here an AI model can be used to compute the stock risk 
    # # (the model can be called to predict the risk in the given dataset and the "Stock Risk" columne created using the model predictions
    # # for the sake of this example we will use a simple equasion to compute the risk
    # df["Stock Risk"] = np.where(
    #     (df["Retailer number of units in stock"] + df["Current number of units in DK warehouse"]) < df["Forecast sales for next 4 weeks"],
    #     "High", "Low"
    # )

    # # Add hover information
    # df["Hover Info"] = df["ISBN"].astype(str) + " - " + df["Product title"]


    # # Title
    # st.header("Stock vs Forecast Sales")

    # # Define color mapping
    # color_mapping = {"High": "red", "Low": "green"}
   
    # # Create an interactive hvPlot scatter plot
    # scatter_plot = df.hvplot.scatter(
    #     x="Selected Stock",
    #     y="Forecast sales for next 4 weeks",
    #     c=df["Stock Risk"].map(color_mapping),  # Map colors
    #     by="Stock Risk",
    #     hover_cols=["ISBN", "Product title"],
    #     title="Stock vs Forecast Sales",
    #     xlabel=stock_option,
    #     ylabel="Forecast Sales (Next 4 Weeks)",
    #     width=800,
    #     height=500
    # ).opts(
    #     legend_position="top_right",  # Ensures legend is always visible
    # )

    # # Display plot in Streamlit
    # st.bokeh_chart(hvplot.render(scatter_plot)) 

    # # Generate Inventory Report
    # st.header("Automated Inventory Report")
    # report = df.groupby("Brand").agg({
    #     "Retailer sales out last week": "sum",
    #     "Retailer number of units in stock": "sum",
    #     "Current number of units in DK warehouse": "sum",
    #     "Forecast sales for next 4 weeks": "sum"
    # }).reset_index()

    # st.dataframe(report)

    # # Option to download report
    # csv = report.to_csv(index=False).encode("utf-8")
    # st.download_button("Download Report", csv, "inventory_report.csv", "text/csv")
  

if __name__ == "__main__":
    main()



