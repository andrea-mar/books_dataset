import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import hvplot.pandas  
import streamlit.components.v1 as components
from io import BytesIO
from bokeh.plotting import figure, save
from bokeh.io import output_file


# This is to make hvplot work in streamlit
def use_file_for_bokeh(chart: figure, chart_height=500):
    output_file('bokeh_graph.html')
    save(chart)
    with open("bokeh_graph.html", 'r', encoding='utf-8') as f:
        html = f.read()
    components.html(html, height=chart_height)

# Set page configuration
st.set_page_config(
    page_title="Book Inventory Risk Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to classify inventory risk
def classify_inventory_risk(df):
    """
    Classify books into risk categories based on predefined business rules.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing book inventory data
    
    Returns:
    pandas.DataFrame: The same DataFrame with added risk classification
    """
    # Create necessary derived metrics
    df['weeks_until_stockout'] = df['Retailer number of units in stock'] / df['Forecast sales for this week'].replace(0, 1)
    df['dk_warehouse_to_weekly_sales_ratio'] = df['Current number of units in DK warehouse'] / df['Retailer sales out last week'].replace(0, 1)
    df['total_available_to_12wk_forecast'] = (df['Retailer number of units in stock'] + df['Current number of units in DK warehouse']) / df['Forecast sales for next 12 weeks'].replace(0, 1)
    df['stock_to_weekly_sales_ratio'] = df['Retailer number of units in stock'] / df['Retailer sales out last week'].replace(0, 1)
    df['ordered_vs_forecasted'] = df['Number of units reatiler has ordered from DK'] / df['Forecast sales for next 4 weeks'].replace(0, 1)
    
    # Apply rules to classify risks
    conditions = [
        # High stockout risk condition
        (df['weeks_until_stockout'] < 2) & (df['dk_warehouse_to_weekly_sales_ratio'] < 4),
        
        # Overstocking risk condition
        (df['total_available_to_12wk_forecast'] > 20) | 
        ((df['stock_to_weekly_sales_ratio'] > 12) & (df['ordered_vs_forecasted'] > 1.5))
    ]
    choices = ['high_stockout_risk', 'overstocking_risk']
    df['risk_category'] = np.select(conditions, choices, default='normal')
    
    return df

 # Load the dataset

@st.cache_data
def load_data():
    return pd.read_excel('data/2025 Feb Data for recruitment task (1).xlsx')

# Function to create risk distribution chart
def create_risk_distribution_chart(df):
    """
    Create a bar chart showing the distribution of risk categories.
    
    Parameters:
    df (pandas.DataFrame): DataFrame with risk categories
    
    Returns:
    matplotlib.figure.Figure: The generated figure
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.countplot(data=df, x='risk_category', ax=ax)
    ax.set_title('Distribution of Risk Categories', fontsize=15)
    ax.set_xlabel('Risk Category', fontsize=12)
    ax.set_ylabel('Number of Books', fontsize=12)
    ax.tick_params(axis='x', rotation=0)
    plt.tight_layout()
    return fig

# Function to create inventory vs. sales chart
def create_inventory_sales_chart(df):
    """
    Create a scatter plot showing inventory vs. sales colored by risk category.
    
    Parameters:
    df (pandas.DataFrame): DataFrame with inventory, sales, and risk data
    
    Returns:
    matplotlib.figure.Figure: The generated figure
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.scatterplot(
        data=df,
        x='Retailer sales out last week',
        y='Retailer number of units in stock',
        hue='risk_category',
        alpha=0.6,
        ax=ax
    )
    ax.set_title('Inventory vs. Sales by Risk Category', fontsize=15)
    ax.set_xlabel('Weekly Sales', fontsize=12)
    ax.set_ylabel('Units in Stock', fontsize=12)
    plt.tight_layout()
    return fig

def create_inventory_sales_chart_hv(df):
    """
    Create an interactive scatter plot showing inventory vs. sales colored by risk category
    using hvPlot.
    
    Parameters:
    df (pandas.DataFrame): DataFrame with inventory, sales, and risk data
    
    Returns:
    hvPlot scatter plot rendered as a Bokeh figure
    """
    
    # Add hover information
    df["Hover Info"] = df["ISBN"].astype(str) + " - " + df["Product title"]

    # Map risk categories to colors
    color_mapping = {
        "high_stockout_risk": "red", 
        "overstocking_risk": "orange",
        "normal": "green"
    }
    
    # Create a new column for plotting
    df["Selected Stock"] = df["Retailer number of units in stock"]
    
    # Create an interactive hvPlot scatter plot
    scatter_plot = df.hvplot.scatter(
        x="Selected Stock",
        y="Forecast sales for next 4 weeks",
        c=df["risk_category"].map(color_mapping),  # Map colors
        by="risk_category",
        hover_cols=["ISBN", "Product title"],
        title="Stock vs Forecast Sales",
        xlabel="Units in Stock",
        ylabel="Forecast Sales (Next 4 Weeks)",
        width=800,
        height=500
    ).opts(
        legend_position="top_right",  # Ensures legend is always visible
    )

    return scatter_plot

# Function to convert dataframe to Excel for download
def to_excel(df):
    """
    Convert DataFrame to Excel file for download.
    
    Parameters:
    df (pandas.DataFrame): DataFrame to convert
    
    Returns:
    bytes: Excel file as bytes
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
    return output.getvalue()


# Main app
def main():
    st.bokeh_chart = use_file_for_bokeh
    st.title("Book Inventory Risk Dashboard")
    
    # st.sidebar.header("Dashboard Controls")
    
    # Load data
    with st.spinner("Loading data..."):
        df = load_data()
        df = classify_inventory_risk(df)
    
    # Summary metrics
    st.header("Inventory Risk Overview")
    col1, col2, col3 = st.columns(3)
    
    # Risk counts
    risk_counts = df['risk_category'].value_counts()
    
    with col1:
        st.metric("Total Books", f"{len(df):,}")
    
    with col2:
        high_risk_count = risk_counts.get('high_stockout_risk', 0)
        st.metric("Stockout Risk", f"{high_risk_count:,}", 
                  delta=f"{high_risk_count/len(df)*100:.1f}%")
    
    with col3:
        overstock_count = risk_counts.get('overstocking_risk', 0)
        st.metric("Overstock Risk", f"{overstock_count:,}", 
                  delta=f"{overstock_count/len(df)*100:.1f}%")
    
    # # Financial impact estimates
    # st.subheader("Estimated Financial Impact")
    # fin_col1, fin_col2 = st.columns(2)
    
    # with fin_col1:
    #     avg_book_cost = 15  # Assume average cost per book
    #     potential_savings = risk_counts.get('overstocking_risk', 0) * avg_book_cost * 0.3  # Assume 30% reduction possible
    #     st.metric("Potential Savings from Resolving Overstock", f"${potential_savings:,.2f}")
    
    # with fin_col2:
    #     avg_book_price = 25  # Assume average selling price
    #     revenue_at_risk = risk_counts.get('high_stockout_risk', 0) * avg_book_price * 0.5  # Assume 50% could be lost sales
    #     st.metric("Revenue at Risk from Stockouts", f"${revenue_at_risk:,.2f}", 
    #               delta=f"-${revenue_at_risk:,.2f}", delta_color="inverse")
    
    # Visualization tabs
    st.header("Risk Visualizations")
    tab1, tab2 = st.tabs(["Risk Distribution", "Inventory vs. Sales"])
    
    with tab1:
        st.subheader("Distribution of Risk Categories")
        risk_fig = create_risk_distribution_chart(df)
        st.pyplot(risk_fig)
    
    with tab2:
        st.subheader("Inventory vs. Sales by Risk Category")
        sales_plot = create_inventory_sales_chart_hv(df)
        st.bokeh_chart(hvplot.render(sales_plot))
    
    # Risk tables with download options
    st.header("Detailed Risk Tables")
    risk_tab1, risk_tab2 = st.tabs(["High Stockout Risk", "Overstocking Risk"])
    
    # High stockout risk table
    with risk_tab1:
        high_risk_books = df[df['risk_category'] == 'high_stockout_risk']
        if not high_risk_books.empty:
            st.subheader(f"Books with High Stockout Risk ({len(high_risk_books):,})")
            
            # Columns to display
            columns_to_show = ['ISBN', 'Product title', 'Brand', 'Retailer sales out last week', 
                               'Retailer number of units in stock', 'Current number of units in DK warehouse',
                               'weeks_until_stockout', 'Forecast sales for this week']
            
            st.dataframe(high_risk_books[columns_to_show])
            
            # Download button
            excel_data = to_excel(high_risk_books[columns_to_show])
            st.download_button(
                label="Download High Stockout Risk Data",
                data=excel_data,
                file_name="high_stockout_risk.xlsx",
                mime="application/vnd.ms-excel"
            )
        else:
            st.info("No books with high stockout risk found.")
    
    # Overstocking risk table
    with risk_tab2:
        overstock_books = df[df['risk_category'] == 'overstocking_risk']
        if not overstock_books.empty:
            st.subheader(f"Books with Overstocking Risk ({len(overstock_books):,})")
            
            # Columns to display
            columns_to_show = ['ISBN', 'Product title', 'Brand', 'Retailer number of units in stock',
                               'Current number of units in DK warehouse', 'Forecast sales for next 12 weeks',
                               'total_available_to_12wk_forecast']
            
            st.dataframe(overstock_books[columns_to_show])
            
            # Download button
            excel_data = to_excel(overstock_books[columns_to_show])
            st.download_button(
                label="Download Overstocking Risk Data",
                data=excel_data,
                file_name="overstocking_risk.xlsx",
                mime="application/vnd.ms-excel"
            )
        else:
            st.info("No books with overstocking risk found.")
    
    # Data filters section
    st.header("Custom Filters")
    st.write("Apply filters to explore specific segments of your inventory:")
    
    # Create expandable filter section
    with st.expander("Show Filters"):
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            # Filter by publisher
            publishers = sorted(df['Brand'].unique())
            selected_publishers = st.multiselect("Select Publishers", publishers)
            
            # Filter by weeks until stockout
            min_weeks, max_weeks = st.slider(
                "Weeks Until Stockout Range", 
                min_value=0.0, 
                max_value=float(df['weeks_until_stockout'].max()), 
                value=(0.0, float(df['weeks_until_stockout'].max()))
            )
        
        with filter_col2:
            # Filter by print status
            status_options = sorted(df['Print status'].unique())
            selected_status = st.multiselect("Print Status", status_options)
            
            # Filter by publication date
            min_date, max_date = st.date_input(
                "Publication Date Range",
                value=[df['Pub Date'].min().date(), df['Pub Date'].max().date()]
            )
        
        # Apply filters button
        if st.button("Apply Filters"):
            filtered_df = df.copy()
            
            # Apply selected filters
            if selected_publishers:
                filtered_df = filtered_df[filtered_df['Brand'].isin(selected_publishers)]
            
            if selected_status:
                filtered_df = filtered_df[filtered_df['Print status'].isin(selected_status)]
            
            filtered_df = filtered_df[
                (filtered_df['weeks_until_stockout'] >= min_weeks) & 
                (filtered_df['weeks_until_stockout'] <= max_weeks)
            ]
            
            filtered_df = filtered_df[
                (filtered_df['Pub Date'].dt.date >= min_date) & 
                (filtered_df['Pub Date'].dt.date <= max_date)
            ]
            
            st.subheader("Filtered Results")
            st.write(f"Found {len(filtered_df):,} books matching your criteria")
            
            # Show filtered data
            st.dataframe(filtered_df[['ISBN', 'Product title', 'Brand', 'Pub Date', 
                                      'Retailer number of units in stock', 'Current number of units in DK warehouse', 'risk_category']])
            
            # Download filtered data
            excel_data = to_excel(filtered_df)
            st.download_button(
                label="Download Filtered Data",
                data=excel_data,
                file_name="filtered_inventory_data.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Footer with info
    st.markdown("---")
    st.markdown("**Book Inventory Risk Analysis Dashboard** | Last updated: February 24, 2025")
    st.markdown(
        "This dashboard uses rule-based classification to identify inventory risks. "
        "High stockout risk books have less than 2 weeks of inventory and limited warehouse stock. "
        "Overstocking risk books have more than 20 weeks of total inventory relative to forecast demand."
    )

if __name__ == "__main__":
    main()