# Standard library imports
import datetime
from datetime import datetime

# Data manipulation and analysis
import pandas as pd
import numpy as np

# Visualization
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Streamlit
import streamlit as st

# Set page title and layout
st.set_page_config(page_title="AMS Dashboard", layout="wide", page_icon="📊")

# At the top with other imports
from database import get_deposito_balance_data, get_savings_balance_data, get_product_branch_mappings

def calculate_delta_percentage(current, previous):
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

# Replace the data loading section
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    with st.spinner('Loading data...'):
        deposito_data = get_deposito_balance_data()
        saving_data = get_savings_balance_data()
        saving_products, deposito_products, branches = get_product_branch_mappings()
    return deposito_data, saving_data, saving_products, deposito_products, branches

# Load data
deposito_data, saving_data, saving_products, deposito_products, branches = load_data()

# Sidebar
with st.sidebar:
    st.logo("logo.png", size="large")
    st.title("AMS Dashboard")
    
    # Set fixed end date to June 30, 2021
    end_date = datetime(2021, 6, 30)
    start_date = end_date - pd.DateOffset(month=1)
    
    # Date inputs
    start_date_input = st.date_input(
        "Periode Awal",
        value=start_date,
        key="start_date"
    )
    
    end_date_input = st.date_input(
        "Periode Akhir",
        value=end_date,
        key="end_date",
        max_value=end_date  # Prevent selecting dates after June 30, 2021
    )
    
    # Date validation
    if start_date_input > end_date_input:
        st.error("Error: End date must fall after start date.")
        st.stop()
    
    # Time period selector with Indonesian terms
    time_period = st.selectbox("Satuan Analisis:", ["Hari", "Minggu", "Bulan", "Tahun"], key="overview_period")
    
    # Filter Branch
    all_branches = deposito_data['KodeCabang'].unique()
    branch_options = {code: branches.get(code, code) for code in all_branches}
    selected_items = st.pills(
        "Filter Cabang:", 
        options=all_branches,
        format_func=lambda x: branch_options[x],
        selection_mode="multi",
        default=all_branches,
        key="sidebar_branch_selector"
    )
    if not selected_items:  # If no branch is selected
        st.warning("Please select at least one branch.")
        st.stop()
    branch_deposito = deposito_data[deposito_data['KodeCabang'].isin(selected_items)]
    branch_saving = saving_data[saving_data['KodeCabang'].isin(selected_items)]

# Create tabs (moved outside sidebar)
funding_tab, lending_tab = st.tabs(["Funding", "Lending"])

with funding_tab:
    #Tab title
    st.title("AMS Funding Dashboard")
    
    # Move product selection here
    deposito_products_list = deposito_data['KodeProduk'].unique()
    saving_products_list = saving_data['KodeProduk'].unique()
    all_products = np.union1d(deposito_products_list, saving_products_list)
    
    # Combine both product mappings
    product_options = {
        code: (saving_products.get(code) or deposito_products.get(code) or code) 
        for code in all_products
    }
    
    selected_products = st.pills(
        "Filter Produk:", 
        options=all_products,
        format_func=lambda x: product_options[x],
        selection_mode="multi",
        default=all_products,
        key="funding_product_selector"
    )
    if not selected_products:  # If no product is selected
        st.warning("Please select at least one product.")
        st.stop()
    
    # After the existing product selection code
    selected_saving_products = [p for p in selected_products if p in saving_products_list]
    selected_deposito_products = [p for p in selected_products if p in deposito_products_list]

    if deposito_data is not None and saving_data is not None:
        # Filter data based on selected date range
        mask = (deposito_data['Tanggal'] >= pd.Timestamp(start_date_input)) & \
            (deposito_data['Tanggal'] <= pd.Timestamp(end_date_input))
        deposito_data = deposito_data[mask]
        
        saving_mask = (saving_data['Tanggal'] >= pd.Timestamp(start_date_input)) & \
                    (saving_data['Tanggal'] <= pd.Timestamp(end_date_input))
        saving_data = saving_data[saving_mask]
        
        # Combined Branch and Product filtering
        filtered_deposito = deposito_data[
            (deposito_data['KodeCabang'].isin(selected_items)) & 
            (deposito_data['KodeProduk'].isin(selected_products))
        ]
        filtered_saving = saving_data[
            (saving_data['KodeCabang'].isin(selected_items)) & 
            (saving_data['KodeProduk'].isin(selected_products))
        ]
    else:
        st.error("No data available. Please check the database connection.")

    # Calculate key metrics using fully filtered data
    total_deposito = int(filtered_deposito.groupby('Tanggal')['Nominal'].sum().iloc[-1] / 1_000_000) if not filtered_deposito.empty else 0
    total_saving = int(filtered_saving.groupby('Tanggal')['Nominal'].sum().iloc[-1] / 1_000_000) if not filtered_saving.empty else 0
    total_dpk = total_deposito + total_saving
    casa_ratio = (total_saving / total_dpk * 100) if total_dpk != 0 else 0

    # Get previous values (from start date)
    prev_deposito = int(filtered_deposito.groupby('Tanggal')['Nominal'].sum().iloc[0] / 1_000_000) if not filtered_deposito.empty else 0
    prev_saving = int(filtered_saving.groupby('Tanggal')['Nominal'].sum().iloc[0] / 1_000_000) if not filtered_saving.empty else 0
    prev_dpk = prev_deposito + prev_saving
    prev_casa = (prev_saving / prev_dpk * 100) if prev_dpk != 0 else 0

    # Calculate delta percentages
    dpk_delta = calculate_delta_percentage(total_dpk, prev_dpk)
    saving_delta = calculate_delta_percentage(total_saving, prev_saving)
    deposito_delta = calculate_delta_percentage(total_deposito, prev_deposito)
    casa_delta = calculate_delta_percentage(casa_ratio, prev_casa)

    
    # Display Total DPK in full width
    st.metric(
        "Total DPK", 
        f"Rp {total_dpk:,.0f} Juta", 
        delta=f"{dpk_delta:+.1f}% dari periode awal",
        delta_color="normal",
        border=1
    )
    
    # Display other metrics in three columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Tabungan", 
            f"Rp {total_saving:,.0f} Juta",
            delta=f"{saving_delta:+.1f}% dari periode awal",
            border=1
        )
    with col2:
        st.metric(
            "Total Deposito", 
            f"Rp {total_deposito:,.0f} Juta",
            delta=f"{deposito_delta:+.1f}% dari periode awal",
            border=1
        )
    with col3:
        st.metric(
            "CASA Ratio", 
            f"{casa_ratio:.1f}%",
            delta=f"{casa_delta:+.1f}% dari periode awal",
            border=1,
            help="CASA Ratio is the ratio of total savings to total deposits and savings."
        )

    # Main Graph Section
    with st.container(border=True):
        # Funding Overview Section
        st.subheader("Grafik Pertumbuhan DPK")
        
        # Aggregate data based on time period
        if time_period == "Hari":                
            branch_deposito = filtered_deposito.groupby([pd.Grouper(key='Tanggal', freq='D')])['Nominal'].sum().reset_index()
            branch_saving = filtered_saving.groupby([pd.Grouper(key='Tanggal', freq='D')])['Nominal'].sum().reset_index()
        elif time_period == "Minggu":                
            branch_deposito = filtered_deposito.groupby([pd.Grouper(key='Tanggal', freq='W-MON')])['Nominal'].sum().reset_index()
            branch_saving = filtered_saving.groupby([pd.Grouper(key='Tanggal', freq='W-MON')])['Nominal'].sum().reset_index()
        elif time_period == "Bulan":
            branch_deposito = filtered_deposito.groupby([pd.Grouper(key='Tanggal', freq='M')])['Nominal'].sum().reset_index()
            branch_saving = filtered_saving.groupby([pd.Grouper(key='Tanggal', freq='M')])['Nominal'].sum().reset_index()
        elif time_period == "Tahun":
            branch_deposito = filtered_deposito.groupby([pd.Grouper(key='Tanggal', freq='Y')])['Nominal'].sum().reset_index()
            branch_saving = filtered_saving.groupby([pd.Grouper(key='Tanggal', freq='Y')])['Nominal'].sum().reset_index()

        # Create combined stacked bar chart
        fig = go.Figure()

        if not filtered_deposito.empty:
            fig.add_bar(
                name='Deposito', 
                x=branch_deposito['Tanggal'], 
                y=branch_deposito['Nominal'],
                marker_color='#1f77b4'
            )

        if not filtered_saving.empty:
            fig.add_bar(
                name='Tabungan', 
                x=branch_saving['Tanggal'], 
                y=branch_saving['Nominal'],
                marker_color='#f3e708'
            )

        # Update layout
        fig.update_layout(
            barmode='stack',
            title=f'Nilai Saldo DPK per {time_period}' + 
                  (' (Deposito Only)' if not selected_saving_products else '') +
                  (' (Savings Only)' if not selected_deposito_products else ''),
            yaxis_title='Nominal Amount',
            legend_title='Product Type',
            showlegend=True
        )

        # Add message if no data
        if filtered_deposito.empty and filtered_saving.empty:
            fig.add_annotation(
                text="No data available for selected products",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )

        st.plotly_chart(fig, use_container_width=True)
        
        # Add summary table
        st.markdown("##### Ringkasan Pertumbuhan DPK")
        
        # Calculate summary statistics
        def get_summary_stats(data):
            if data.empty:
                return 0, 0, 0, 0
            awal = data.iloc[0]['Nominal']
            akhir = data.iloc[-1]['Nominal']
            selisih = akhir - awal
            pertumbuhan = (selisih / awal * 100) if awal != 0 else 0
            return awal, akhir, selisih, pertumbuhan

        # Get stats for each type
        deposito_awal, deposito_akhir, deposito_selisih, deposito_growth = get_summary_stats(branch_deposito)
        saving_awal, saving_akhir, saving_selisih, saving_growth = get_summary_stats(branch_saving)
        
        # Calculate total DPK stats
        dpk_awal = deposito_awal + saving_awal
        dpk_akhir = deposito_akhir + saving_akhir
        dpk_selisih = dpk_akhir - dpk_awal
        dpk_growth = (dpk_selisih / dpk_awal * 100) if dpk_awal != 0 else 0

        # Create summary dataframe
        summary_data = {
            'Kategori': ['Deposito', 'Tabungan', 'Total DPK'],
            'Periode Awal': [
                f"Rp {deposito_awal/1_000_000:,.2f} Juta",
                f"Rp {saving_awal/1_000_000:,.2f} Juta",
                f"Rp {dpk_awal/1_000_000:,.2f} Juta"
            ],
            'Periode Akhir': [
                f"Rp {deposito_akhir/1_000_000:,.2f} Juta",
                f"Rp {saving_akhir/1_000_000:,.2f} Juta",
                f"Rp {dpk_akhir/1_000_000:,.2f} Juta"
            ],
            'Perubahan': [
                f"Rp {deposito_selisih/1_000_000:,.2f} Juta",
                f"Rp {saving_selisih/1_000_000:,.2f} Juta",
                f"Rp {dpk_selisih/1_000_000:,.2f} Juta"
            ],
            'Pertumbuhan': [
                f"{deposito_growth:,.2f}%",
                f"{saving_growth:,.2f}%",
                f"{dpk_growth:,.2f}%"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(
            summary_df,
            hide_index=True,
            use_container_width=True
        )

        # Growth Overview Section
        st.markdown("---")  # Add separator
        st.subheader("Grafik Perubahan DPK")
        
        # Create columns for displaying the parameters
        growth_unit = st.radio("Unit:", ("Percentage", "Nominal"))
    
        # Calculate growth for both products
        def calculate_growth(df, unit='Percentage'):
            # Calculate period-over-period growth
            growth = df.copy()
            growth['Growth'] = df['Nominal'].diff()
            if unit == 'Percentage':
                growth['Growth'] = (growth['Growth'] / df['Nominal'].shift(1)) * 100
            return growth.dropna()  # Remove first row since it has no growth rate
        
        # Calculate DPK by combining saving and deposito data
        dpk_data = pd.DataFrame()
        dpk_data['Tanggal'] = branch_deposito['Tanggal']
        dpk_data['Nominal'] = branch_deposito['Nominal'] + branch_saving['Nominal']
        
        # Get growth data for all products
        deposito_growth = calculate_growth(branch_deposito, growth_unit)
        saving_growth = calculate_growth(branch_saving, growth_unit)
        dpk_growth = calculate_growth(dpk_data, growth_unit)
        
        # Create growth chart
        fig_growth = go.Figure()
        
        # Add lines for all products
        fig_growth.add_scatter(
            name='Deposito',
            x=deposito_growth['Tanggal'],
            y=deposito_growth['Growth'],
            line=dict(color='#1f77b4', width=2)
        )
        fig_growth.add_scatter(
            name='Tabungan',
            x=saving_growth['Tanggal'],
            y=saving_growth['Growth'],
            line=dict(color='#f3e708', width=2)
        )
        fig_growth.add_scatter(
            name='Total DPK',
            x=dpk_growth['Tanggal'],
            y=dpk_growth['Growth'],
            line=dict(color='#f48322', width=4) 
        )
        
        # Update layout
        y_title = f"Perubahan ({' % ' if growth_unit == 'Percentage' else ' Nominal '})"
        fig_growth.update_layout(
            title=f'Perubahan DPK per {time_period}',
            yaxis_title=y_title,
            xaxis_title='Periode',
            showlegend=True,
            legend_title='Product Type'
        )
        
        # Add zero line for reference
        fig_growth.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        st.plotly_chart(fig_growth, use_container_width=True)
        
        st.markdown("---")

        # Inside the Main Graph Section, after the charts
        with st.expander("Tampilkan Rincian Saldo DPK"):
            # Create combined dataframe with all data points
            combined_data = pd.DataFrame({
                'Date': branch_deposito['Tanggal'],
                'Deposito': branch_deposito['Nominal'],
                'Tabungan': branch_saving['Nominal'],
                'Total DPK': branch_deposito['Nominal'] + branch_saving['Nominal'],
                'Deposito Growth': deposito_growth['Growth'],
                'Tabungan Growth': saving_growth['Growth'],
                'DPK Growth': dpk_growth['Growth']
            })
            
            # Format the date column to DD/MM/YYYY
            combined_data['Date'] = combined_data['Date'].dt.strftime('%d/%m/%Y')
            
            # Format funding numbers to millions and add thousand separators
            combined_data['Deposito'] = combined_data['Deposito'].apply(lambda x: f"Rp {x/1_000_000:,.2f} Juta")
            combined_data['Tabungan'] = combined_data['Tabungan'].apply(lambda x: f"Rp {x/1_000_000:,.2f} Juta")
            combined_data['Total DPK'] = combined_data['Total DPK'].apply(lambda x: f"Rp {x/1_000_000:,.2f} Juta")
            
            # Format growth numbers based on growth unit
            if growth_unit == "Percentage":
                combined_data['Deposito Growth'] = combined_data['Deposito Growth'].apply(lambda x: f"{x:.2f}%")
                combined_data['Tabungan Growth'] = combined_data['Tabungan Growth'].apply(lambda x: f"{x:.2f}%")
                combined_data['DPK Growth'] = combined_data['DPK Growth'].apply(lambda x: f"{x:.2f}%")
            else:
                combined_data['Deposito Growth'] = combined_data['Deposito Growth'].apply(lambda x: f"Rp {x/1_000_000:,.2f} Juta")
                combined_data['Tabungan Growth'] = combined_data['Tabungan Growth'].apply(lambda x: f"Rp {x/1_000_000:,.2f} Juta")
                combined_data['DPK Growth'] = combined_data['DPK Growth'].apply(lambda x: f"Rp {x/1_000_000:,.2f} Juta")
            
            st.dataframe(
                combined_data,
                column_config={
                    "Date": "Tanggal",
                },
                hide_index=True
            )

    # Proportion Charts
    with st.container(border=True):
        st.subheader("Grafik Proporsi DPK")
        view_by = st.radio("Tipe Proporsi:", ("Cabang", "Produk"), key="saving_view")
        col1, col2 = st.columns(2)
        with col1:
            if view_by == "Cabang":
                saving_grouped = filtered_saving.groupby('KodeCabang')['Nominal'].sum()
                saving_grouped.index = saving_grouped.index.map(lambda x: branches.get(x, x))
            else:
                saving_grouped = filtered_saving.groupby('KodeProduk')['Nominal'].sum()
                saving_grouped.index = saving_grouped.index.map(lambda x: saving_products.get(x, x))
            
            fig_saving = px.pie(values=saving_grouped.values, names=saving_grouped.index, hole=0.6)
            fig_saving.update_layout(
                title=f"Proporsi Tabungan per {view_by}"
            )
            fig_saving.add_annotation(text="Tabungan", x=0.5, y=0.5, font_size=20, showarrow=False)
            st.plotly_chart(fig_saving)

        with col2:
            if view_by == "Cabang":
                deposito_grouped = filtered_deposito.groupby('KodeCabang')['Nominal'].sum()
                deposito_grouped.index = deposito_grouped.index.map(lambda x: branches.get(x, x))
            else:
                deposito_grouped = filtered_deposito.groupby('KodeProduk')['Nominal'].sum()
                deposito_grouped.index = deposito_grouped.index.map(lambda x: deposito_products.get(x, x))
            
            fig_deposito = px.pie(values=deposito_grouped.values, names=deposito_grouped.index, hole=0.6)
            fig_deposito.update_layout(
                title=f"Proporsi Deposito per {view_by}"
            )
            fig_deposito.add_annotation(text="Deposito", x=0.5, y=0.5, font_size=20, showarrow=False)
            st.plotly_chart(fig_deposito)

        # Add Combined Proportion Table
        with st.expander("Tampilkan Rincian Data Produk"):
            # Create pivot tables for both savings and deposito
            saving_pivot = pd.pivot_table(
                filtered_saving,
                values='Nominal',
                index='KodeProduk',
                columns='KodeCabang',
                aggfunc='sum',
                fill_value=0
            )
            
            deposito_pivot = pd.pivot_table(
                filtered_deposito,
                values='Nominal',
                index='KodeProduk',
                columns='KodeCabang',
                aggfunc='sum',
                fill_value=0
            )
            
            # Map codes to names
            saving_pivot.index = saving_pivot.index.map(lambda x: f"Tabungan - {saving_products.get(x, x)}")
            deposito_pivot.index = deposito_pivot.index.map(lambda x: f"Deposito - {deposito_products.get(x, x)}")
            
            # Combine the pivot tables
            combined_pivot = pd.concat([saving_pivot, deposito_pivot])
            
            # Map branch codes to names
            combined_pivot.columns = combined_pivot.columns.map(lambda x: branches.get(x, x))
            
            # Add product totals as a new column
            combined_pivot['Total Product'] = combined_pivot.sum(axis=1)
            
            # Add subtotals for Saving and Deposito
            saving_total = pd.DataFrame(
                combined_pivot[combined_pivot.index.str.startswith('Tabungan')].sum()
            ).T
            saving_total.index = ['Total Tabungan']
            
            deposito_total = pd.DataFrame(
                combined_pivot[combined_pivot.index.str.startswith('Deposito')].sum()
            ).T
            deposito_total.index = ['Total Deposito']
            
            # Add grand total
            total_row = pd.DataFrame(
                combined_pivot.sum()
            ).T
            total_row.index = ['Total DPK']
            
            # Combine everything
            final_pivot = pd.concat([
                combined_pivot,
                saving_total,
                deposito_total,
                total_row
            ])
            
            # Format values to millions with thousand separators
            formatted_final_pivot = final_pivot.applymap(lambda x: f"Rp {x/1_000_000:,.2f} Juta")
            
            # Display the table
            st.dataframe(
                formatted_final_pivot,
                use_container_width=True
            )

    # Branch Comparison
    with st.container(border=True):
        st.subheader("Perbandingan Funding Cabang")
        col1, col2 = st.columns(2)
        with col1:
            branch_options = {code: branches.get(code, code) for code in deposito_data['KodeCabang'].unique()}
            branch1 = st.selectbox(
                "Pilih Cabang 1:", 
                options=list(branch_options.keys()),
                format_func=lambda x: branch_options[x]
            )
        with col2:
            branch2 = st.selectbox(
                "Pilih Cabang 2:", 
                options=list(branch_options.keys()),
                format_func=lambda x: branch_options[x]
            )

        # Filter data for selected branches
        def get_branch_data(branch_code):
            branch_deposito = filtered_deposito[filtered_deposito['KodeCabang'] == branch_code]
            branch_saving = filtered_saving[filtered_saving['KodeCabang'] == branch_code]
            
            # Get initial and final values
            total_deposito = int(branch_deposito.groupby('Tanggal')['Nominal'].sum().iloc[-1] / 1_000_000) if not branch_deposito.empty else 0
            total_saving = int(branch_saving.groupby('Tanggal')['Nominal'].sum().iloc[-1] / 1_000_000) if not branch_saving.empty else 0
            total_dpk = total_deposito + total_saving
            
            total_deposito_awal = int(branch_deposito.groupby('Tanggal')['Nominal'].sum().iloc[0] / 1_000_000) if not branch_deposito.empty else 0
            total_saving_awal = int(branch_saving.groupby('Tanggal')['Nominal'].sum().iloc[0] / 1_000_000) if not branch_saving.empty else 0
            total_dpk_awal = total_deposito_awal + total_saving_awal
            
            # Get product breakdowns
            deposito_by_product = branch_deposito.groupby('KodeProduk')['Nominal'].sum()
            saving_by_product = branch_saving.groupby('KodeProduk')['Nominal'].sum()
            
            return {
                'total_dpk': total_dpk,
                'total_deposito': total_deposito,
                'total_saving': total_saving,
                'total_dpk_awal': total_dpk_awal,
                'total_deposito_awal': total_deposito_awal,
                'total_saving_awal': total_saving_awal,
                'deposito_by_product': deposito_by_product,
                'saving_by_product': saving_by_product
            }

        # Get data for both branches
        branch1_data = get_branch_data(branch1)
        branch2_data = get_branch_data(branch2)

        # Replace metrics with summary table
        summary_data = pd.DataFrame({
            'Metric': ['Total DPK', 'Total Tabungan', 'Total Deposito'],
            f'{branches.get(branch1, branch1)} Awal': [
                f"Rp {branch1_data['total_dpk_awal']:,.0f} Juta",
                f"Rp {branch1_data['total_saving_awal']:,.0f} Juta", 
                f"Rp {branch1_data['total_deposito_awal']:,.0f} Juta"
            ],
            f'{branches.get(branch1, branch1)} Akhir': [
                f"Rp {branch1_data['total_dpk']:,.0f} Juta",
                f"Rp {branch1_data['total_saving']:,.0f} Juta",
                f"Rp {branch1_data['total_deposito']:,.0f} Juta"
            ],
            f'{branches.get(branch1, branch1)} Pertumbuhan': [
                f"Rp {(branch1_data['total_dpk'] - branch1_data['total_dpk_awal']):,.0f} Juta ({((branch1_data['total_dpk'] - branch1_data['total_dpk_awal'])/branch1_data['total_dpk_awal']*100 if branch1_data['total_dpk_awal'] != 0 else 0):,.1f}%)",
                f"Rp {(branch1_data['total_saving'] - branch1_data['total_saving_awal']):,.0f} Juta ({((branch1_data['total_saving'] - branch1_data['total_saving_awal'])/branch1_data['total_saving_awal']*100 if branch1_data['total_saving_awal'] != 0 else 0):,.1f}%)",
                f"Rp {(branch1_data['total_deposito'] - branch1_data['total_deposito_awal']):,.0f} Juta ({((branch1_data['total_deposito'] - branch1_data['total_deposito_awal'])/branch1_data['total_deposito_awal']*100 if branch1_data['total_deposito_awal'] != 0 else 0):,.1f}%)"
            ],
            f'{branches.get(branch2, branch2)} Awal': [
                f"Rp {branch2_data['total_dpk_awal']:,.0f} Juta",
                f"Rp {branch2_data['total_saving_awal']:,.0f} Juta",
                f"Rp {branch2_data['total_deposito_awal']:,.0f} Juta"
            ],
            f'{branches.get(branch2, branch2)} Akhir': [
                f"Rp {branch2_data['total_dpk']:,.0f} Juta",
                f"Rp {branch2_data['total_saving']:,.0f} Juta",
                f"Rp {branch2_data['total_deposito']:,.0f} Juta"
            ],
            f'{branches.get(branch2, branch2)} Pertumbuhan': [
                f"Rp {(branch2_data['total_dpk'] - branch2_data['total_dpk_awal']):,.0f} Juta ({((branch2_data['total_dpk'] - branch2_data['total_dpk_awal'])/branch2_data['total_dpk_awal']*100 if branch2_data['total_dpk_awal'] != 0 else 0):,.1f}%)",
                f"Rp {(branch2_data['total_saving'] - branch2_data['total_saving_awal']):,.0f} Juta ({((branch2_data['total_saving'] - branch2_data['total_saving_awal'])/branch2_data['total_saving_awal']*100 if branch2_data['total_saving_awal'] != 0 else 0):,.1f}%)",
                f"Rp {(branch2_data['total_deposito'] - branch2_data['total_deposito_awal']):,.0f} Juta ({((branch2_data['total_deposito'] - branch2_data['total_deposito_awal'])/branch2_data['total_deposito_awal']*100 if branch2_data['total_deposito_awal'] != 0 else 0):,.1f}%)"
            ]
        })
        st.dataframe(summary_data, hide_index=True, use_container_width=True)

        # Replace stacked bar with pie charts
        col1, col2 = st.columns(2)
        
        def create_pie_charts(branch_data, branch_name):
            # Create subplots for Tabungan and Deposito
            fig = make_subplots(rows=1, cols=2, specs=[[{'type':'pie'}, {'type':'pie'}]], 
                               subplot_titles=('Komposisi Tabungan', 'Komposisi Deposito'))

            # Tabungan pie
            if branch_data['total_saving'] > 0:
                fig.add_trace(
                    go.Pie(
                        labels=[saving_products.get(x, x) for x in branch_data['saving_by_product'].index],
                        values=branch_data['saving_by_product'].values,
                        textinfo='percent+label',
                        textposition='inside',
                        hole=0.3
                    ),
                    row=1, col=1
                )

            # Deposito pie
            if branch_data['total_deposito'] > 0:
                fig.add_trace(
                    go.Pie(
                        labels=[deposito_products.get(x, x) for x in branch_data['deposito_by_product'].index],
                        values=branch_data['deposito_by_product'].values,
                        textinfo='percent+label',
                        textposition='inside',
                        hole=0.3
                    ),
                    row=1, col=2
                )

            fig.update_layout(
                title=f"Komposisi DPK {branch_name}",
                height=400,
                showlegend=False
            )
            
            return fig

        with col1:
            fig1 = create_pie_charts(branch1_data, branches.get(branch1, branch1))
            st.plotly_chart(fig1, use_container_width=True, key="branch1_pies")
            
        with col2:
            fig2 = create_pie_charts(branch2_data, branches.get(branch2, branch2))
            st.plotly_chart(fig2, use_container_width=True, key="branch2_pies")
        
        # Create comparison dataframe
        comparison_data = []
        
        def format_difference(value):
            return f"Rp {value:,.2f} Juta"

        def get_product_data(branch_data, product_code, is_saving):
            if is_saving:
                data = branch_data[branch_data['KodeProduk'] == product_code]
            else:
                data = branch_data[branch_data['KodeProduk'] == product_code]
            
            awal = int(data.groupby('Tanggal')['Nominal'].sum().iloc[0] / 1_000_000) if not data.empty else 0
            akhir = int(data.groupby('Tanggal')['Nominal'].sum().iloc[-1] / 1_000_000) if not data.empty else 0
            selisih = akhir - awal
            pertumbuhan = (selisih / awal * 100) if awal != 0 else 0
            
            return awal, akhir, selisih, pertumbuhan

        # Add saving products comparison
        all_saving_products = set(branch1_data['saving_by_product'].index) | set(branch2_data['saving_by_product'].index)
        for product in all_saving_products:
            product_name = f"Tabungan - {saving_products.get(product, product)}"
            awal1, akhir1, selisih1, pertumbuhan1 = get_product_data(filtered_saving[filtered_saving['KodeCabang'] == branch1], product, True)
            awal2, akhir2, selisih2, pertumbuhan2 = get_product_data(filtered_saving[filtered_saving['KodeCabang'] == branch2], product, True)
            
            comparison_data.append({
                'Product': product_name,
                f'{branches.get(branch1, branch1)} Awal': f"Rp {awal1:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Akhir': f"Rp {akhir1:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Pertumbuhan': f"Rp {selisih1:,.2f} Juta ({pertumbuhan1:.1f}%)",
                f'{branches.get(branch2, branch2)} Awal': f"Rp {awal2:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Akhir': f"Rp {akhir2:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Pertumbuhan': f"Rp {selisih2:,.2f} Juta ({pertumbuhan2:.1f}%)",
                '_akhir1': akhir1,  # Hidden columns for plotting
                '_akhir2': akhir2
            })

        # Add deposito products comparison (similar structure)
        all_deposito_products = set(branch1_data['deposito_by_product'].index) | set(branch2_data['deposito_by_product'].index)
        for product in all_deposito_products:
            product_name = f"Deposito - {deposito_products.get(product, product)}"
            awal1, akhir1, selisih1, pertumbuhan1 = get_product_data(filtered_deposito[filtered_deposito['KodeCabang'] == branch1], product, False)
            awal2, akhir2, selisih2, pertumbuhan2 = get_product_data(filtered_deposito[filtered_deposito['KodeCabang'] == branch2], product, False)
            
            comparison_data.append({
                'Product': product_name,
                f'{branches.get(branch1, branch1)} Awal': f"Rp {awal1:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Akhir': f"Rp {akhir1:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Pertumbuhan': f"Rp {selisih1:,.2f} Juta ({pertumbuhan1:.1f}%)",
                f'{branches.get(branch2, branch2)} Awal': f"Rp {awal2:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Akhir': f"Rp {akhir2:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Pertumbuhan': f"Rp {selisih2:,.2f} Juta ({pertumbuhan2:.1f}%)",
                '_akhir1': akhir1,  # Hidden columns for plotting
                '_akhir2': akhir2
            })

        # Add totals (similar structure, without the hidden columns)
        comparison_data.extend([
            {
                'Product': 'Total Tabungan',
                f'{branches.get(branch1, branch1)} Awal': f"Rp {branch1_data['total_saving_awal']:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Akhir': f"Rp {branch1_data['total_saving']:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Pertumbuhan': f"Rp {(branch1_data['total_saving'] - branch1_data['total_saving_awal']):,.2f} Juta ({((branch1_data['total_saving'] - branch1_data['total_saving_awal'])/branch1_data['total_saving_awal']*100 if branch1_data['total_saving_awal'] != 0 else 0):,.1f}%)",
                f'{branches.get(branch2, branch2)} Awal': f"Rp {branch2_data['total_saving_awal']:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Akhir': f"Rp {branch2_data['total_saving']:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Pertumbuhan': f"Rp {(branch2_data['total_saving'] - branch2_data['total_saving_awal']):,.2f} Juta ({((branch2_data['total_saving'] - branch2_data['total_saving_awal'])/branch2_data['total_saving_awal']*100 if branch2_data['total_saving_awal'] != 0 else 0):,.1f}%)",
                '_akhir1': branch2_data['total_saving'],  # Hidden columns for plotting
                '_akhir2': branch2_data['total_saving']
            },
            {
                'Product': 'Total Deposito',
                f'{branches.get(branch1, branch1)} Awal': f"Rp {branch1_data['total_deposito_awal']:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Akhir': f"Rp {branch1_data['total_deposito']:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Pertumbuhan': f"Rp {(branch1_data['total_deposito'] - branch1_data['total_deposito_awal']):,.2f} Juta ({((branch1_data['total_deposito'] - branch1_data['total_deposito_awal'])/branch1_data['total_deposito_awal']*100 if branch1_data['total_deposito_awal'] != 0 else 0):,.1f}%)",
                f'{branches.get(branch2, branch2)} Awal': f"Rp {branch2_data['total_deposito_awal']:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Akhir': f"Rp {branch2_data['total_deposito']:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Pertumbuhan': f"Rp {(branch2_data['total_deposito'] - branch2_data['total_deposito_awal']):,.2f} Juta ({((branch2_data['total_deposito'] - branch2_data['total_deposito_awal'])/branch2_data['total_deposito_awal']*100 if branch2_data['total_deposito_awal'] != 0 else 0):,.1f}%)",
                '_akhir1': branch2_data['total_deposito'],  # Hidden columns for plotting
                '_akhir2': branch2_data['total_deposito']
            },
            {
                'Product': 'Total DPK',
                f'{branches.get(branch1, branch1)} Awal': f"Rp {branch1_data['total_dpk_awal']:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Akhir': f"Rp {branch1_data['total_dpk']:,.2f} Juta",
                f'{branches.get(branch1, branch1)} Pertumbuhan': f"Rp {(branch1_data['total_dpk'] - branch1_data['total_dpk_awal']):,.2f} Juta ({((branch1_data['total_dpk'] - branch1_data['total_dpk_awal'])/branch1_data['total_dpk_awal']*100 if branch1_data['total_dpk_awal'] != 0 else 0):,.1f}%)",
                f'{branches.get(branch2, branch2)} Awal': f"Rp {branch2_data['total_dpk_awal']:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Akhir': f"Rp {branch2_data['total_dpk']:,.2f} Juta",
                f'{branches.get(branch2, branch2)} Pertumbuhan': f"Rp {(branch2_data['total_dpk'] - branch2_data['total_dpk_awal']):,.2f} Juta ({((branch2_data['total_dpk'] - branch2_data['total_dpk_awal'])/branch2_data['total_dpk_awal']*100 if branch2_data['total_dpk_awal'] != 0 else 0):,.1f}%)",
                '_akhir1': branch2_data['total_dpk'],  # Hidden columns for plotting
                '_akhir2': branch2_data['total_dpk']
            }
        ])

        # Create DataFrame and display table (excluding hidden columns)
        comparison_df = pd.DataFrame(comparison_data)
        visible_columns = [col for col in comparison_df.columns if not col.startswith('_')]

        # First show the bar chart
        st.markdown("##### Perbandingan Produk Funding per Cabang")
        fig = go.Figure()

        # Filter out totals for the chart
        product_data = comparison_df[~comparison_df['Product'].isin(['Total Tabungan', 'Total Deposito', 'Total DPK'])]

        fig.add_trace(go.Bar(
            name=branches.get(branch1, branch1),
            x=product_data['Product'],
            y=product_data['_akhir1'],
            text=[f"Rp {x:,.0f} Juta" for x in product_data['_akhir1']],
            textposition='auto',
        ))

        fig.add_trace(go.Bar(
            name=branches.get(branch2, branch2),
            x=product_data['Product'],
            y=product_data['_akhir2'],
            text=[f"Rp {x:,.0f} Juta" for x in product_data['_akhir2']],
            textposition='auto',
        ))

        fig.update_layout(
            barmode='group',
            height=400,
            xaxis_tickangle=-45,
            showlegend=True,
            legend_title="Cabang"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Then show the detailed comparison table
        st.markdown("##### Perbandingan Detail Produk")
        st.dataframe(comparison_df[visible_columns], hide_index=True, use_container_width=True)

with lending_tab:
    st.subheader("Lending Overview")
    st.info("Lending data visualization will be implemented here. You'll need to add the lending data and create corresponding visualizations.")
    
    # Placeholder for lending metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Loans", "Rp 0 Juta", border=1)
    with col2:
        st.metric("NPL Ratio", "0%", border=1)
    with col3:
        st.metric("LDR", "0%", border=1)