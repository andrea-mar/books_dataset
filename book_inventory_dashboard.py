import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64

# Set page config
st.set_page_config(page_title="Book Inventory Dashboard", layout="wide")

# Function to download dataframe as Excel
def download_excel(df, filename="report.xlsx"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Report', index=False)
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel</a>'
    return href

# Main dashboard layout
st.title("📚 Book Inventory Analytics Dashboard")

# Sidebar for filters
st.sidebar.header("Filters")

# File uploader for Excel
uploaded_file = st.sidebar.file_uploader("Upload your inventory Excel file", type=['xlsx', 'xls'])

if uploaded_file is not None:
    # Load the data
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
        
        # Convert date columns to datetime
        try:
            df['Pub Date'] = pd.to_datetime(df['Pub Date'])
            if 'Reprint Date' in df.columns:
                df['Reprint Date'] = pd.to_datetime(df['Reprint Date'])
        except:
            st.warning("Date conversion error. Please ensure date columns are in correct format.")
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        st.stop()
else:
    st.info("Please upload an Excel file to begin analysis.")
    st.stop()



# Additional filters
selected_brands = st.sidebar.multiselect(
    "Select Brands", 
    options=sorted(df['Brand'].unique()),
    default=sorted(df['Brand'].unique())[:5]
)

date_range = st.sidebar.date_input(
    "Publication Date Range",
    value=(df['Pub Date'].min().date(), df['Pub Date'].max().date())
)

print_status_options = st.sidebar.multiselect(
    "Print Status",
    options=sorted(df['Print status'].unique()),
    default=sorted(df['Print status'].unique())
)

min_stock, max_stock = st.sidebar.slider(
    "Units in Stock Range",
    int(df['Retailer number of units in stock'].min()),
    int(df['Retailer number of units in stock'].max()),
    (int(df['Retailer number of units in stock'].min()), int(df['Retailer number of units in stock'].max()))
)

# Filter the data based on selections
filtered_df = df[
    (df['Brand'].isin(selected_brands)) &
    (df['Pub Date'].dt.date >= date_range[0]) &
    (df['Pub Date'].dt.date <= date_range[1]) &
    (df['Print status'].isin(print_status_options)) &
    (df['Retailer number of units in stock'] >= min_stock) &
    (df['Retailer number of units in stock'] <= max_stock)
]

# Show number of filtered items
st.sidebar.markdown(f"### Filtered Items: {len(filtered_df)}")

# Report selection
st.sidebar.header("Report Selection")
report_type = st.sidebar.selectbox(
    "Select Report Type",
    ["Overview", "Inventory Health", "Sales Forecast", "Stock Replenishment", "Custom Report"]
)

# Main content area based on report selection
if len(filtered_df) == 0:
    st.warning("No data matches your filter criteria. Please adjust the filters.")
    st.stop()

# Overview Report
if report_type == "Overview":
    st.header("Inventory Overview")
    
    # KPI metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_titles = len(filtered_df)
        st.metric("Total Titles", f"{total_titles:,}")
    
    with col2:
        total_units = filtered_df['Retailer number of units in stock'].sum()
        st.metric("Total Units in Stock", f"{total_units:,}")
    
    with col3:
        avg_sales = filtered_df['Retailer sales out last week'].mean()
        st.metric("Avg Weekly Sales", f"{avg_sales:.1f}")
    
    with col4:
        total_warehouse = filtered_df['Current number of units in DK warehouse'].sum()
        st.metric("Warehouse Stock", f"{total_warehouse:,}")
    
    # Brand distribution chart
    st.subheader("Titles by Brand")
    brand_counts = filtered_df['Brand'].value_counts().reset_index()
    brand_counts.columns = ['Brand', 'Count']
    
    fig_brands = px.bar(
        brand_counts.head(10),
        x='Brand',
        y='Count',
        color='Count',
        color_continuous_scale='Blues'
    )
    fig_brands.update_layout(height=400)
    st.plotly_chart(fig_brands, use_container_width=True)
    
    # Stock analysis by print status
    st.subheader("Inventory by Print Status")
    print_status_pivot = filtered_df.groupby('Print status').agg({
        'Retailer number of units in stock': 'sum',
        'Current number of units in DK warehouse': 'sum',
        'ISBN': 'count'
    }).reset_index()
    print_status_pivot.columns = ['Print Status', 'Retail Stock', 'Warehouse Stock', 'Title Count']
    
    fig_status = px.bar(
        print_status_pivot,
        x='Print Status',
        y=['Retail Stock', 'Warehouse Stock'],
        barmode='group',
        title='Stock Levels by Print Status'
    )
    st.plotly_chart(fig_status, use_container_width=True)
    
    # Publication timeline
    st.subheader("Publication Timeline")
    
    # Group by month and count titles
    filtered_df['Pub Month'] = filtered_df['Pub Date'].dt.to_period('M')
    pub_timeline = filtered_df.groupby('Pub Month').size().reset_index()
    pub_timeline.columns = ['Pub Month', 'Title Count']
    pub_timeline['Pub Month'] = pub_timeline['Pub Month'].dt.to_timestamp()
    
    fig_timeline = px.line(
        pub_timeline,
        x='Pub Month',
        y='Title Count',
        title='New Titles by Publication Month'
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

# Inventory Health Report
elif report_type == "Inventory Health":
    st.header("Inventory Health Analysis")
    
    # Calculate weeks of supply
    filtered_df['Calculated WOS'] = filtered_df['Retailer number of units in stock'] / filtered_df['Forecast sales for this week'].clip(lower=0.1)
    
    # WOS distribution
    st.subheader("Weeks of Supply Distribution")
    
    wos_bins = [0, 4, 8, 12, 16, 20, 24, float('inf')]
    wos_labels = ['0-4 weeks', '4-8 weeks', '8-12 weeks', '12-16 weeks', 
                  '16-20 weeks', '20-24 weeks', '24+ weeks']
    
    filtered_df['WOS Category'] = pd.cut(
        filtered_df['Calculated WOS'], 
        bins=wos_bins, 
        labels=wos_labels
    )
    
    wos_counts = filtered_df['WOS Category'].value_counts().reset_index()
    wos_counts.columns = ['WOS Category', 'Title Count']
    
    fig_wos = px.pie(
        wos_counts,
        values='Title Count',
        names='WOS Category',
        color_discrete_sequence=px.colors.sequential.Blues,
        title='Title Distribution by Weeks of Supply'
    )
    fig_wos.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_wos, use_container_width=True)
    
    # Stock health by brand
    st.subheader("Stock Health by Brand")
    
    brand_health = filtered_df.groupby('Brand').agg({
        'Calculated WOS': 'mean',
        'Retailer number of units in stock': 'sum',
        'Forecast sales for next 4 weeks': 'sum',
        'ISBN': 'count'
    }).reset_index()
    
    brand_health.columns = ['Brand', 'Avg WOS', 'Total Stock', 'Forecast 4-Week Sales', 'Title Count']
    brand_health['Stock Coverage Ratio'] = brand_health['Total Stock'] / brand_health['Forecast 4-Week Sales']
    brand_health.sort_values('Avg WOS', ascending=False, inplace=True)
    
    fig_brand_health = px.scatter(
        brand_health.head(15),
        x='Forecast 4-Week Sales',
        y='Total Stock',
        size='Title Count',
        color='Avg WOS',
        hover_name='Brand',
        color_continuous_scale='Blues',
        title='Brand Stock Position vs Forecast Demand'
    )
    
    # Add optimal coverage line
    x_range = [brand_health['Forecast 4-Week Sales'].min(), brand_health['Forecast 4-Week Sales'].max()]
    fig_brand_health.add_trace(
        go.Scatter(
            x=x_range,
            y=[x*8/4 for x in x_range],  # 8 weeks of stock line
            mode='lines',
            line=dict(color='green', dash='dash'),
            name='8 Weeks Target'
        )
    )
    
    st.plotly_chart(fig_brand_health, use_container_width=True)
    
    # Low stock alert table
    st.subheader("Low Stock Alert")
    
    low_stock_df = filtered_df[filtered_df['Calculated WOS'] < 4].sort_values('Calculated WOS')
    
    if len(low_stock_df) > 0:
        display_cols = ['ISBN', 'Product title', 'Brand', 'Retailer number of units in stock', 
                        'Forecast sales for this week', 'Calculated WOS', 'Print status']
        st.dataframe(low_stock_df[display_cols], height=400)
        
        st.markdown(download_excel(low_stock_df[display_cols], "low_stock_report.xlsx"), unsafe_allow_html=True)
    else:
        st.info("No titles with critically low stock.")

# Sales Forecast Report
elif report_type == "Sales Forecast":
    st.header("Sales Forecast Analysis")
    
    # Forecast overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        this_week = filtered_df['Forecast sales for this week'].sum()
        st.metric("Forecast Sales This Week", f"{this_week:,.0f}")
    
    with col2:
        next_4weeks = filtered_df['Forecast sales for next 4 weeks'].sum()
        st.metric("Forecast Next 4 Weeks", f"{next_4weeks:,.0f}")
    
    with col3:
        next_12weeks = filtered_df['Forecast sales for next 12 weeks'].sum()
        st.metric("Forecast Next 12 Weeks", f"{next_12weeks:,.0f}")
    
    # Top titles by forecast
    st.subheader("Top 10 Titles by 12-Week Forecast")
    
    top_forecast = filtered_df.sort_values('Forecast sales for next 12 weeks', ascending=False).head(10)
    top_forecast_display = top_forecast[['Product title', 'Brand', 'Forecast sales for this week', 
                                         'Forecast sales for next 4 weeks', 'Forecast sales for next 12 weeks']]
    
    fig_top_forecast = px.bar(
        top_forecast,
        x='Product title',
        y='Forecast sales for next 12 weeks',
        color='Brand',
        title='Top Titles by 12-Week Sales Forecast'
    )
    fig_top_forecast.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_top_forecast, use_container_width=True)
    
    # Brand forecast comparison
    st.subheader("Forecast by Brand")
    
    brand_forecast = filtered_df.groupby('Brand').agg({
        'Forecast sales for this week': 'sum',
        'Forecast sales for next 4 weeks': 'sum',
        'Forecast sales for next 12 weeks': 'sum',
        'ISBN': 'count'
    }).reset_index()
    
    brand_forecast.sort_values('Forecast sales for next 12 weeks', ascending=False, inplace=True)
    brand_forecast_display = brand_forecast.head(10)
    
    # Calculate weekly average rates
    brand_forecast_display['Weekly Rate (4 weeks)'] = brand_forecast_display['Forecast sales for next 4 weeks'] / 4
    brand_forecast_display['Weekly Rate (12 weeks)'] = brand_forecast_display['Forecast sales for next 12 weeks'] / 12
    
    fig_brand_forecast = px.bar(
        brand_forecast_display,
        x='Brand',
        y=['Weekly Rate (4 weeks)', 'Weekly Rate (12 weeks)'],
        barmode='group',
        title='Weekly Sales Rate by Brand: 4-Week vs 12-Week Forecast'
    )
    st.plotly_chart(fig_brand_forecast, use_container_width=True)
    
    # Forecast vs current stock
    st.subheader("Forecast Coverage Analysis")
    
    filtered_df['Stock Coverage (weeks)'] = filtered_df['Retailer number of units in stock'] / (
        filtered_df['Forecast sales for next 12 weeks'] / 12).clip(lower=0.1)
    
    coverage_buckets = ['Under-stocked (<4 weeks)', 'Balanced (4-12 weeks)', 'Over-stocked (>12 weeks)']
    filtered_df['Coverage Category'] = pd.cut(
        filtered_df['Stock Coverage (weeks)'],
        bins=[0, 4, 12, float('inf')],
        labels=coverage_buckets
    )
    
    coverage_counts = filtered_df['Coverage Category'].value_counts().reset_index()
    coverage_counts.columns = ['Category', 'Title Count']
    
    fig_coverage = px.pie(
        coverage_counts,
        values='Title Count',
        names='Category',
        color_discrete_sequence=['#FF9999', '#66B2FF', '#99FF99'],
        title='Title Distribution by Stock Coverage'
    )
    fig_coverage.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_coverage, use_container_width=True)

# Stock Replenishment Report
elif report_type == "Stock Replenishment":
    st.header("Stock Replenishment Planning")
    
    # Filter to only include titles that need attention
    filtered_df['Weeks Coverage'] = filtered_df['Retailer number of units in stock'] / (
        filtered_df['Forecast sales for next 4 weeks'] / 4).clip(lower=0.1)
    
    # Reprint candidates
    st.subheader("Reprint Candidates")
    
    reprint_candidates = filtered_df[
        (filtered_df['Weeks Coverage'] < 6) &
        (filtered_df['Current number of units in DK warehouse'] < filtered_df['Forecast sales for next 4 weeks']) &
        (filtered_df['Print status'] != 'Out of Print')
    ].sort_values('Weeks Coverage')
    
    if len(reprint_candidates) > 0:
        # Calculate recommended reprint quantity
        reprint_candidates['Recommended Reprint'] = (
            reprint_candidates['Forecast sales for next 12 weeks'] * 1.5 -
            reprint_candidates['Retailer number of units in stock'] -
            reprint_candidates['Current number of units in DK warehouse']
        ).clip(lower=0)
        
        reprint_display = reprint_candidates[[
            'ISBN', 'Product title', 'Brand', 'Print status',
            'Retailer number of units in stock', 'Current number of units in DK warehouse',
            'Forecast sales for next 12 weeks', 'Weeks Coverage', 'Recommended Reprint'
        ]].head(20)
        
        st.dataframe(reprint_display, height=400)
        st.markdown(download_excel(reprint_display, "reprint_candidates.xlsx"), unsafe_allow_html=True)
    else:
        st.info("No titles currently qualify as reprint candidates based on current criteria.")
    
    # Stock redistribution opportunities
    st.subheader("Warehouse to Retail Distribution Opportunities")
    
    redistribution_candidates = filtered_df[
        (filtered_df['Weeks Coverage'] < 8) &
        (filtered_df['Current number of units in DK warehouse'] > filtered_df['Forecast sales for next 4 weeks'] * 0.5)
    ].sort_values('Weeks Coverage')
    
    if len(redistribution_candidates) > 0:
        redistribution_candidates['Recommended Transfer'] = (
            (redistribution_candidates['Forecast sales for next 4 weeks'] * 2) -
            redistribution_candidates['Retailer number of units in stock']
        ).clip(lower=0).clip(upper=redistribution_candidates['Current number of units in DK warehouse'])
        
        redistribution_display = redistribution_candidates[[
            'ISBN', 'Product title', 'Brand',
            'Retailer number of units in stock', 'Current number of units in DK warehouse',
            'Forecast sales for next 4 weeks', 'Weeks Coverage', 'Recommended Transfer'
        ]].head(20)
        
        st.dataframe(redistribution_display, height=400)
        st.markdown(download_excel(redistribution_display, "redistribution_opportunities.xlsx"), unsafe_allow_html=True)
    else:
        st.info("No redistribution opportunities identified based on current criteria.")
    
    # Titles with upcoming reprints
    st.subheader(f"Scheduled Reprints")

    upcoming_reprints = filtered_df[filtered_df['Reprint Date'].notna()].sort_values('Reprint Date')
    
    if len(upcoming_reprints) > 0:
        upcoming_display = upcoming_reprints[[
            'ISBN', 'Product title', 'Brand', 'Retailer number of units in stock',
            'Current number of units in DK warehouse', 'Reprint Quantity', 'Reprint Date'
        ]]
        
        st.dataframe(upcoming_display, height=400)
    else:
        st.info("No upcoming reprints scheduled in the system.")

# Custom Report
elif report_type == "Custom Report":
    st.header("Custom Report Builder")
    
    # Column selection
    st.subheader("Select Columns for Your Report")
    
    all_columns = filtered_df.columns.tolist()
    selected_columns = st.multiselect(
        "Choose columns to include",
        options=all_columns,
        default=['ISBN', 'Product title', 'Brand', 'Pub Date', 'Retailer number of units in stock', 
                'Current number of units in DK warehouse', 'Forecast sales for next 4 weeks']
    )
    
    # Sorting options
    st.subheader("Sorting Options")
    
    sort_column = st.selectbox(
        "Sort by column",
        options=selected_columns if selected_columns else all_columns
    )
    
    sort_ascending = st.checkbox("Sort ascending", value=False)
    
    # Additional calculations
    st.subheader("Add Calculated Fields")
    
    add_wos = st.checkbox("Add Weeks of Supply calculation")
    add_coverage_ratio = st.checkbox("Add Stock Coverage Ratio")
    add_reprint_recommendation = st.checkbox("Add Reprint Recommendation")
    
    # Build the report dataframe
    if selected_columns:
        report_df = filtered_df[selected_columns].copy()
        
        # Add calculated columns if selected
        if add_wos and 'Retailer number of units in stock' in selected_columns and 'Forecast sales for this week' in selected_columns:
            report_df['Weeks of Supply'] = report_df['Retailer number of units in stock'] / report_df['Forecast sales for this week'].clip(lower=0.1)
        
        if add_coverage_ratio and 'Retailer number of units in stock' in selected_columns and 'Forecast sales for next 4 weeks' in selected_columns:
            report_df['4-Week Coverage Ratio'] = report_df['Retailer number of units in stock'] / report_df['Forecast sales for next 4 weeks']
        
        if add_reprint_recommendation and 'Retailer number of units in stock' in selected_columns and 'Current number of units in DK warehouse' in selected_columns and 'Forecast sales for next 12 weeks' in selected_columns:
            report_df['Reprint Recommendation'] = (
                report_df['Forecast sales for next 12 weeks'] * 1.2 - 
                report_df['Retailer number of units in stock'] - 
                report_df['Current number of units in DK warehouse']
            ).clip(lower=0)
        
        # Sort the dataframe
        report_df = report_df.sort_values(sort_column, ascending=sort_ascending)
        
        # Show the report
        st.subheader("Custom Report Output")
        st.dataframe(report_df, height=500)
        
        # Download options
        st.subheader("Download Options")
        report_name = st.text_input("Report filename", "custom_inventory_report")
        if not report_name.endswith('.xlsx'):
            report_name += '.xlsx'
        
        st.markdown(download_excel(report_df, report_name), unsafe_allow_html=True)
        
        # Quick visualization
        st.subheader("Quick Visualization")
        
        viz_type = st.selectbox(
            "Visualization type",
            ["Bar Chart", "Scatter Plot", "Pie Chart"]
        )
        
        numeric_columns = report_df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = report_df.select_dtypes(include=['object']).columns.tolist()
        
        if viz_type == "Bar Chart" and numeric_columns and categorical_columns:
            bar_x = st.selectbox("X-axis (Category)", options=categorical_columns)
            bar_y = st.selectbox("Y-axis (Value)", options=numeric_columns)
            
            # Group by selected category and calculate mean of selected value
            bar_data = report_df.groupby(bar_x)[bar_y].mean().reset_index()
            bar_data = bar_data.sort_values(bar_y, ascending=False).head(10)
            
            fig_bar = px.bar(
                bar_data,
                x=bar_x,
                y=bar_y,
                title=f"Average {bar_y} by {bar_x}"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        elif viz_type == "Scatter Plot" and len(numeric_columns) >= 2:
            scatter_x = st.selectbox("X-axis", options=numeric_columns, index=0)
            scatter_y = st.selectbox("Y-axis", options=numeric_columns, index=min(1, len(numeric_columns)-1))
            color_by = st.selectbox("Color by", options=['None'] + categorical_columns)
            
            if color_by == 'None':
                fig_scatter = px.scatter(
                    report_df,
                    x=scatter_x,
                    y=scatter_y,
                    title=f"{scatter_y} vs {scatter_x}"
                )
            else:
                fig_scatter = px.scatter(
                    report_df,
                    x=scatter_x,
                    y=scatter_y,
                    color=color_by,
                    title=f"{scatter_y} vs {scatter_x} by {color_by}"
                )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        elif viz_type == "Pie Chart" and categorical_columns:
            pie_category = st.selectbox("Category", options=categorical_columns)
            
            pie_data = report_df[pie_category].value_counts().reset_index()
            pie_data.columns = [pie_category, 'Count']
            
            fig_pie = px.pie(
                pie_data.head(10),
                values='Count',
                names=pie_category,
                title=f"Distribution by {pie_category}"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
    else:
        st.warning("Please select at least one column for your report.")

# Add footer with timestamp
st.markdown("---")
st.markdown(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")