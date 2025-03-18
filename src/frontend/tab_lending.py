import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.backend.database_lending import get_lending_data
from src.backend.database_product import get_lending_product_mapping
from src.backend.database_branch import get_branch_mapping
from src.component.calculation import calculate_delta_percentage, calculate_ratio
from src.backend.database_group import get_grup1_mapping, get_grup2_mapping

def calculate_delta_percentage(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def show_lending_tab():
    """Main function to display the lending dashboard tab"""
    # Ensure session state values are up to date
    if 'start_date' not in st.session_state or 'end_date' not in st.session_state:
        st.error("Session state missing date values. Please refresh the page.")
        return
        
    # Get data from database with session state dates
    financing_data, rahn_data = get_lending_data(
        start_date=pd.to_datetime(st.session_state.start_date),
        end_date=pd.to_datetime(st.session_state.end_date)
    )
    
    # Add error handling for database connection
    if financing_data is None or rahn_data is None:
        st.error("Unable to fetch data from database. Please check your database connection.")
        return
    
    # Check if dataframes are empty or don't have required columns
    if financing_data.empty or 'Tanggal' not in financing_data.columns:
        st.warning("No financing data available for the selected period")
        # Create empty dataframe with required columns
        financing_data = pd.DataFrame(columns=['Tanggal', 'KodeCabang', 'KodeProduk', 'Kolektibilitas', 
                                              'JmlPencairan', 'ByrPokok', 'Outstanding', 'KdStsPemb',
                                              'KodeGrup1', 'KodeGrup2', 'KdKolektor'])
    else:
        # Convert Tanggal column to datetime
        financing_data['Tanggal'] = pd.to_datetime(financing_data['Tanggal'])
    
    if rahn_data.empty or 'Tanggal' not in rahn_data.columns:
        st.warning("No rahn data available for the selected period")
        # Create empty dataframe with required columns
        rahn_data = pd.DataFrame(columns=['Tanggal', 'KodeCabang', 'KodeProduk', 'Nominal', 'Kolektibilitas'])
    else:
        # Convert Tanggal column to datetime
        rahn_data['Tanggal'] = pd.to_datetime(rahn_data['Tanggal'])
    
    # Add this line to convert Kolektibilitas to numeric only if columns exist
    if 'Kolektibilitas' in financing_data.columns:
        financing_data['Kolektibilitas'] = pd.to_numeric(financing_data['Kolektibilitas'], errors='coerce')
    if 'Kolektibilitas' in rahn_data.columns:
        rahn_data['Kolektibilitas'] = pd.to_numeric(rahn_data['Kolektibilitas'], errors='coerce')

    branches = get_branch_mapping()
    financing_products, rahn_products = get_lending_product_mapping()
    
    # Tab title with product information
    st.title("AMS Lending Dashboard")
    
    # Get values from session state - these are guaranteed to be set by the sidebar
    start_date_input = st.session_state.start_date
    end_date_input = st.session_state.end_date
    selected_items = st.session_state.sidebar_branch_selector
    time_period = st.session_state.overview_period
    
    # Remember selected products in session state if available
    default_products = st.session_state.get('lending_product_selector', None)

    # Check if we have any data
    if financing_data.empty and rahn_data.empty:
        st.info("No lending data available for the selected period and branches. Please check your filters or database connection.")
        return

    # Product selection
    financing_products_list = [] if financing_data.empty else financing_data['KodeProduk'].unique()
    rahn_products_list = [] if rahn_data.empty else rahn_data['KodeProduk'].unique()
    all_products = np.union1d(financing_products_list, rahn_products_list)
    
    # Combine both product mappings
    product_options = {
        code: (financing_products.get(code) or rahn_products.get(code) or f"Product {code}") 
        for code in all_products
    }
    
    if len(all_products) == 0:
        st.warning("No products found. Please check your data source.")
        return
    
    # Create widget without modifying session state afterward
    st.subheader("Filter Produk:")
    st.pills(
        label="Pilih Produk:", 
        options=all_products,
        format_func=lambda x: product_options[x],
        selection_mode="multi",
        default=default_products if default_products is not None else all_products,
        key="lending_product_selector"
    )
    
    # Get the selection from session state
    selected_products = st.session_state.lending_product_selector
    
    if not selected_products:
        st.warning("Please select at least one product.")
        st.stop()
    
    # Filter products
    selected_financing_products = [p for p in selected_products if p in financing_products_list]
    selected_rahn_products = [p for p in selected_products if p in rahn_products_list]

    # Filter data based on date range and selections
    if financing_data is not None and rahn_data is not None:
        # Date filtering
        financing_mask = (financing_data['Tanggal'] >= pd.to_datetime(start_date_input)) & \
                        (financing_data['Tanggal'] <= pd.to_datetime(end_date_input))
        financing_data = financing_data[financing_mask]
        
        rahn_mask = (rahn_data['Tanggal'] >= pd.to_datetime(start_date_input)) & \
                   (rahn_data['Tanggal'] <= pd.to_datetime(end_date_input))
        rahn_data = rahn_data[rahn_mask]

        # Branch and Product filtering
        filtered_financing = financing_data[
            (financing_data['KodeCabang'].isin(selected_items)) &
            (financing_data['KodeProduk'].isin(selected_products))
        ]
        
        
        filtered_rahn = rahn_data[
            (rahn_data['KodeCabang'].isin(selected_items)) & 
            (rahn_data['KodeProduk'].isin(selected_products))
        ]
    else:
        st.error("No data available. Please check the database connection.")
        return
    
    # Calculate key metrics
    total_financing = int(filtered_financing.groupby('Tanggal')['Outstanding'].sum().iloc[-1] / 1_000_000) if not filtered_financing.empty else 0
    total_rahn = int(filtered_rahn.groupby('Tanggal')['Nominal'].sum().iloc[-1] / 1_000_000) if not filtered_rahn.empty else 0
    total_lending = total_financing + total_rahn
    
    # Calculate key metrics previous period
    prev_financing = int(filtered_financing.groupby('Tanggal')['Outstanding'].sum().iloc[0] / 1_000_000) if not filtered_financing.empty else 0
    prev_rahn = int(filtered_rahn.groupby('Tanggal')['Nominal'].sum().iloc[0] / 1_000_000) if not filtered_rahn.empty else 0
    prev_lending = prev_financing + prev_rahn
    
    # Calculate NPF (Non-Performing Financing) for current period (end date)
    end_date_financing = filtered_financing[filtered_financing['Tanggal'] == filtered_financing['Tanggal'].max()]
    end_date_rahn = filtered_rahn[filtered_rahn['Tanggal'] == filtered_rahn['Tanggal'].max()]
    
    npf_financing = end_date_financing[end_date_financing['Kolektibilitas'] >= 3]['Outstanding'].sum()
    npf_rahn = end_date_rahn[end_date_rahn['Kolektibilitas'] >= 3]['Nominal'].sum()
    total_outstanding = end_date_financing['Outstanding'].sum() + end_date_rahn['Nominal'].sum()
    total_npf = npf_financing + npf_rahn
    npf_ratio = calculate_ratio(total_npf, total_outstanding)


    # Get previous NPF values (start date)
    start_date_financing = filtered_financing[filtered_financing['Tanggal'] == filtered_financing['Tanggal'].min()]
    start_date_rahn = filtered_rahn[filtered_rahn['Tanggal'] == filtered_rahn['Tanggal'].min()]
    
    prev_npf_financing = start_date_financing[start_date_financing['Kolektibilitas'] >= 3]['Outstanding'].sum()
    prev_npf_rahn = start_date_rahn[start_date_rahn['Kolektibilitas'] >= 3]['Nominal'].sum()
    prev_total_outstanding = start_date_financing['Outstanding'].sum() + start_date_rahn['Nominal'].sum()
    prev_total_npf = prev_npf_financing + prev_npf_rahn
    prev_npf_ratio = calculate_ratio(prev_total_npf, prev_total_outstanding)


    # Calculate delta percentages
    lending_delta = calculate_delta_percentage(total_lending, prev_lending)
    financing_delta = calculate_delta_percentage(total_financing, prev_financing)
    rahn_delta = calculate_delta_percentage(total_rahn, prev_rahn)
    npf_delta = npf_ratio - prev_npf_ratio

    # Display Total Lending in full width
    st.metric(
        "Total Lending", 
        f"Rp {total_lending:,.0f} Juta", 
        delta=f"{lending_delta:+.1f}% dari periode awal",
        delta_color="normal",
        border=1
    )
    
    # Display other metrics in three columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Pembiayaan", 
            f"Rp {total_financing:,.0f} Juta",
            delta=f"{financing_delta:+.1f}% dari periode awal",
            border=1
        )
    with col2:
        st.metric(
            "Total Rahn", 
            f"Rp {total_rahn:,.0f} Juta",
            delta=f"{rahn_delta:+.1f}% dari periode awal",
            border=1
        )
    with col3:
        st.metric(
            "NPF Ratio", 
            f"{npf_ratio:.1f}%",
            delta=f"{npf_delta:+.1f}% dari periode awal",
            border=1,
            help="Non-Performing Financing Ratio"
        )
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([":material/monitoring: Pertumbuhan Lending", ":material/pie_chart: Proporsi Lending", ":material/group: Proporsi Grup Angsuran", ":material/support_agent: Proporsi Kolektor", ":material/compare_arrows: Perbandingan Cabang"])

    # Main Graph Section
    with tab1:
        st.subheader(":material/monitoring: Grafik Pertumbuhan Lending")

        # Aggregate data based on time period
        freq_map = {
            "Hari": 'D',
            "Minggu": 'W-MON',
            "Bulan": 'M',
            "Tahun": 'YE'
        }
        freq = freq_map.get(time_period, 'D')
        
        financing_agg = filtered_financing.groupby([pd.Grouper(key='Tanggal', freq=freq)])['Outstanding'].sum().reset_index()
        rahn_agg = filtered_rahn.groupby([pd.Grouper(key='Tanggal', freq=freq)])['Nominal'].sum().reset_index()

        # Create stacked bar chart
        fig = go.Figure()

        if not filtered_financing.empty:
            fig.add_bar(
                name='Pembiayaan', 
                x=financing_agg['Tanggal'], 
                y=financing_agg['Outstanding'],
                marker_color='#1f77b4'
            )

        if not filtered_rahn.empty:
            fig.add_bar(
                name='Rahn', 
                x=rahn_agg['Tanggal'], 
                y=rahn_agg['Nominal'],
                marker_color='#f3e708'
            )

        fig.update_layout(
            barmode='stack',
            title=f'Nilai Saldo Pembiayaan dan Rahn per {time_period}',
            yaxis_title='Nominal Amount',
            legend_title='Product Type',
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Add summary table below the main graph
        st.markdown("##### Ringkasan Pertumbuhan Lending")
        summary_data = pd.DataFrame({
            'Kategori': ['Pembiayaan', 'Rahn', 'Total Lending'],
            'Periode Awal': [
                f"Rp {prev_financing:,.0f} Juta",
                f"Rp {prev_rahn:,.0f} Juta",
                f"Rp {prev_lending:,.0f} Juta"
            ],
            'Periode Akhir': [
                f"Rp {total_financing:,.0f} Juta",
                f"Rp {total_rahn:,.0f} Juta",
                f"Rp {total_lending:,.0f} Juta"
            ],
            'Perubahan': [
                f"Rp {(total_financing - prev_financing):,.0f} Juta",
                f"Rp {(total_rahn - prev_rahn):,.0f} Juta",
                f"Rp {(total_lending - prev_lending):,.0f} Juta"
            ],
            'Pertumbuhan': [
                f"{financing_delta:,.1f}%",
                f"{rahn_delta:,.1f}%",
                f"{lending_delta:,.1f}%"
            ]
        })
        st.dataframe(summary_data, hide_index=True, use_container_width=True)

        # Growth Trend Section
        st.markdown("----")
        st.subheader(":material/planner_review: Grafik Perubahan Lending")
        

        # Unit selection - Added unique key
        growth_unit = st.radio(
            "Unit:", 
            ("Percentage", "Nominal"),
            key="growth_unit_radio"
        )
        
        # Calculate growth trends
        def calculate_growth(df, value_col, unit='Percentage'):
            growth = df.copy()
            growth['Growth'] = df[value_col].diff()
            if unit == 'Percentage':
                growth['Growth'] = (growth['Growth'] / df[value_col].shift(1)) * 100
            return growth.dropna()
        
        # Aggregate and calculate growth for both types
        financing_growth = calculate_growth(financing_agg, 'Outstanding', growth_unit)
        rahn_growth = calculate_growth(rahn_agg, 'Nominal', growth_unit)
        
        # Calculate total lending growth
        total_agg = pd.DataFrame({
            'Tanggal': financing_agg['Tanggal'],
            'Total': financing_agg['Outstanding'] + rahn_agg['Nominal']
        })
        total_growth = calculate_growth(total_agg, 'Total', growth_unit)
        
        # # Calculate NPF trend
        # npf_agg = filtered_financing.groupby([pd.Grouper(key='Tanggal', freq=freq)]).agg({
        #     'Outstanding': lambda x: (
        #         x[filtered_financing['Kolektibilitas'] >= 3].sum() / x.sum() * 100
        #     )
        # }).reset_index()
        # npf_agg = npf_agg.rename(columns={'Outstanding': 'NPF'})
        
        # Create line chart
        fig = go.Figure()
        
        fig.add_scatter(
            name='Total Lending',
            x=total_growth['Tanggal'],
            y=total_growth['Growth'],
            line=dict(color='#2ecc71', width=2)
        )
        
        fig.add_scatter(
            name='Pembiayaan',
            x=financing_growth['Tanggal'],
            y=financing_growth['Growth'],
            line=dict(color='#1f77b4', width=2)
        )
        
        fig.add_scatter(
            name='Rahn',
            x=rahn_growth['Tanggal'],
            y=rahn_growth['Growth'],
            line=dict(color='#f3e708', width=2)
        )
        
        # fig.add_scatter(
        #     name='NPF',
        #     x=npf_agg['Tanggal'],
        #     y=npf_agg['NPF'],
        #     line=dict(color='#e74c3c', width=2)
        # )
        
        # Add zero line reference
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title=f'Perubahan Lending per {time_period} ({growth_unit})',
            yaxis_title=f'Growth ({"%"if growth_unit=="Percentage" else "Nominal"})',
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed balance table
        with st.expander("Tampilkan Rincian Saldo Lending"):
            detailed_data = pd.DataFrame({
                'Tanggal': financing_agg['Tanggal'].dt.strftime('%d/%m/%Y'),
                'Pembiayaan': financing_agg['Outstanding'],
                'Rahn': rahn_agg['Nominal'],
                'Total': total_agg['Total'],
                # 'NPF': npf_agg['NPF']
            })
            
            # Calculate growth percentages
            detailed_data['% Pembiayaan Growth'] = detailed_data['Pembiayaan'].pct_change(fill_method=None) * 100
            detailed_data['% Rahn Growth'] = detailed_data['Rahn'].pct_change(fill_method=None) * 100
            detailed_data['% Total Growth'] = detailed_data['Total'].pct_change(fill_method=None) * 100
            
            # Format the display
            formatted_data = detailed_data.copy()
            formatted_data['Pembiayaan'] = formatted_data['Pembiayaan'].apply(lambda x: f"Rp {x/1_000_000:,.0f} Juta")
            formatted_data['Rahn'] = formatted_data['Rahn'].apply(lambda x: f"Rp {x/1_000_000:,.0f} Juta")
            formatted_data['Total'] = formatted_data['Total'].apply(lambda x: f"Rp {x/1_000_000:,.0f} Juta")
            # formatted_data['NPF'] = formatted_data['NPF'].apply(lambda x: f"{x:.2f}%")
            formatted_data['% Pembiayaan Growth'] = formatted_data['% Pembiayaan Growth'].apply(lambda x: f"{x:.2f}%")
            formatted_data['% Rahn Growth'] = formatted_data['% Rahn Growth'].apply(lambda x: f"{x:.2f}%")
            formatted_data['% Total Growth'] = formatted_data['% Total Growth'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(formatted_data, hide_index=True, use_container_width=True)

    # Lending Proportion Section
    with tab2:
        st.subheader(":material/pie_chart: Proporsi Lending")

        # Type selection - Added unique key
        proportion_type = st.radio(
            "Tipe Proporsi:", 
            ("Cabang", "Produk"),
            key="proportion_type_radio"
        )
        
        if proportion_type == "Cabang":
            # Calculate branch proportions
            financing_by_branch = filtered_financing.groupby('KodeCabang')['Outstanding'].sum()
            rahn_by_branch = filtered_rahn.groupby('KodeCabang')['Nominal'].sum()
            
            # Create subplots for financing and rahn
            fig = make_subplots(
                rows=1, cols=2,
                specs=[[{"type": "pie"}, {"type": "pie"}]],
                subplot_titles=('Proporsi Pembiayaan per Cabang', 'Proporsi Rahn per Cabang')
            )
            
            # Financing pie chart
            if not financing_by_branch.empty:
                fig.add_trace(
                    go.Pie(
                        labels=[branches.get(code, f"Branch {code}") for code in financing_by_branch.index],
                        values=financing_by_branch.values,
                        textinfo='percent+label',
                        textposition='inside',
                        hole=0.3,
                        name='Pembiayaan'
                    ),
                    row=1, col=1
                )
            
            # Rahn pie chart
            if not rahn_by_branch.empty:
                fig.add_trace(
                    go.Pie(
                        labels=[branches.get(code, f"Branch {code}") for code in rahn_by_branch.index],
                        values=rahn_by_branch.values,
                        textinfo='percent+label',
                        textposition='inside',
                        hole=0.3,
                        name='Rahn'
                    ),
                    row=1, col=2
                )
            
        else:  # Product proportion
            # Calculate product proportions
            financing_by_product = filtered_financing.groupby('KodeProduk')['Outstanding'].sum()
            rahn_by_product = filtered_rahn.groupby('KodeProduk')['Nominal'].sum()
            
            # Create subplots for financing and rahn
            fig = make_subplots(
                rows=1, cols=2,
                specs=[[{"type": "pie"}, {"type": "pie"}]],
                subplot_titles=('Proporsi Pembiayaan per Produk', 'Proporsi Rahn per Produk')
            )
            
            # Financing pie chart
            if not financing_by_product.empty:
                fig.add_trace(
                    go.Pie(
                        labels=[financing_products.get(code, f"Product {code}") for code in financing_by_product.index],
                        values=financing_by_product.values,
                        textinfo='percent+label',
                        textposition='inside',
                        hole=0.3,
                        name='Pembiayaan'
                    ),
                    row=1, col=1
                )
            
            # Rahn pie chart
            if not rahn_by_product.empty:
                fig.add_trace(
                    go.Pie(
                        labels=[rahn_products.get(code, f"Product {code}") for code in rahn_by_product.index],
                        values=rahn_by_product.values,
                        textinfo='percent+label',
                        textposition='inside',
                        hole=0.3,
                        name='Rahn'
                    ),
                    row=1, col=2
                )
        
        # Update layout
        fig.update_layout(
            height=500,
            showlegend=False,
            title_text=f"Proporsi Lending per {proportion_type}"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("Rincian Data Produk Lending"):
            # Get all unique products
            all_financing_products = financing_products.keys()
            all_rahn_products = rahn_products.keys()
            
            # Get all branches
            all_branches = selected_items
            
            # Initialize data structure
            product_data = []
            
            # Process financing products
            for product in all_financing_products:
                row_data = {'Product': f"Pembiayaan - {financing_products.get(product, f'Product {product}')}"}
                total_product = 0
                
                # Calculate per branch values
                for branch in all_branches:
                    branch_value = filtered_financing[
                        (filtered_financing['KodeProduk'] == product) & 
                        (filtered_financing['KodeCabang'] == branch)
                    ]['Outstanding'].sum()
                    row_data[branches.get(branch, branch)] = branch_value
                    total_product += branch_value
                
                # Only add products with non-zero total
                if total_product > 0:
                    row_data['Total'] = total_product
                    product_data.append(row_data)
            
            # Process rahn products
            for product in all_rahn_products:
                row_data = {'Product': f"Rahn - {rahn_products.get(product, f'Product {product}')}"}
                total_product = 0
                
                # Calculate per branch values
                for branch in all_branches:
                    branch_value = filtered_rahn[
                        (filtered_rahn['KodeProduk'] == product) & 
                        (filtered_rahn['KodeCabang'] == branch)
                    ]['Nominal'].sum()
                    row_data[branches.get(branch, branch)] = branch_value
                    total_product += branch_value
                
                # Only add products with non-zero total
                if total_product > 0:
                    row_data['Total'] = total_product
                    product_data.append(row_data)
            
            # Create DataFrame only if there are products with non-zero values
            if product_data:
                summary_df = pd.DataFrame(product_data)
                
                # Calculate totals
                total_pembiayaan_row = {
                    'Product': 'Total Pembiayaan'
                }
                total_rahn_row = {
                    'Product': 'Total Rahn'
                }
                total_lending_row = {
                    'Product': 'Total Lending'
                }
                
                for col in summary_df.columns[1:]:
                    total_pembiayaan_row[col] = summary_df[col][summary_df['Product'].str.startswith('Pembiayaan')].sum()
                    total_rahn_row[col] = summary_df[col][summary_df['Product'].str.startswith('Rahn')].sum()
                    total_lending_row[col] = summary_df[col].sum()
                
                # Add total rows properly
                summary_df = pd.concat([
                    summary_df, 
                    pd.DataFrame([total_pembiayaan_row, total_rahn_row, total_lending_row])
                ], ignore_index=True)
                
                # Format the values
                for col in summary_df.columns[1:]:
                    summary_df[col] = summary_df[col].apply(lambda x: f"Rp {x/1_000_000:,.0f} Juta")
                
                # Display the table
                st.dataframe(summary_df, hide_index=True, use_container_width=True)
            else:
                st.info("No products with non-zero values found for the selected criteria.")

    # Analisis Grup
    with tab3:
        st.subheader(":material/group: Proporsi Pembiayaan per Grup")
        

        # Get unique groups from financing data and their mappings, excluding null values
        groups = sorted(filtered_financing[filtered_financing['KodeGrup1'].notna()]['KodeGrup1'].unique().tolist()) if 'KodeGrup1' in filtered_financing.columns else []
        groups_mapping = get_grup1_mapping()
        
        if groups:
            # Calculate group totals for the latest date
            latest_date = filtered_financing['Tanggal'].max()
            group_data = filtered_financing[filtered_financing['Tanggal'] == latest_date].groupby('KodeGrup1')['Outstanding'].sum().reset_index()
            
            # Sort the data by Outstanding value in descending order and take top 20
            group_data = group_data.sort_values('Outstanding', ascending=False)
            group_data_top20 = group_data.head(20)  # Get top 20 groups
            
            # Calculate the sum of remaining groups
            others_sum = group_data.iloc[20:]['Outstanding'].sum() if len(group_data) > 20 else 0
            
            # Create bar chart data including "Others"
            x_values = [groups_mapping.get(code, f"Group {code}") for code in group_data_top20['KodeGrup1']] + ['Others']
            y_values = list(group_data_top20['Outstanding'] / 1_000_000) + [others_sum / 1_000_000]
            text_values = [f"Rp {val/1_000_000:,.0f} Juta" for val in group_data_top20['Outstanding']] + [f"Rp {others_sum/1_000_000:,.0f} Juta"]
            
            # Create bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=x_values,
                y=y_values,
                text=text_values,
                textposition='auto',
                marker_color=['#1f77b4'] * 20 + ['#7f7f7f']  # Different color for "Others"
            ))
            
            fig.update_layout(
                title='Outstanding per Grup (Top 20 + Others)',
                xaxis_title='Grup',
                yaxis_title='Outstanding (Juta)',
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add detailed table (showing all groups)
            with st.expander("Tampilkan Rincian Data Grup"):
                detailed_group_data = pd.DataFrame({
                    'Grup': [groups_mapping.get(code, f"Group {code}") for code in group_data['KodeGrup1']],
                    'Outstanding': [f"Rp {val/1_000_000:,.0f} Juta" for val in group_data['Outstanding']],
                    'Persentase': [(val/group_data['Outstanding'].sum() * 100) for val in group_data['Outstanding']]
                })
                detailed_group_data['Persentase'] = detailed_group_data['Persentase'].apply(lambda x: f"{x:.2f}%")
                
                # Add total row
                total_row_data = {
                    'Grup': 'Total Pembiayaan',
                    'Outstanding': f"Rp {group_data['Outstanding'].sum()/1_000_000:,.0f} Juta",
                    'Persentase': '100.00%'
                }
                
                # Concatenate the original dataframe with the total row
                detailed_group_data = pd.concat([
                    detailed_group_data, 
                    pd.DataFrame([total_row_data])
                ], ignore_index=True)
                
                st.dataframe(detailed_group_data, hide_index=True, use_container_width=True)
        else:
            st.info("Tidak ada data grup yang tersedia untuk periode yang dipilih.")
            
        st.markdown("---")
        
        st.subheader(":material/payments: Proporsi Pembiayaan per Metode Angsuran")
        # Get unique groups from financing data and their mappings, excluding null values
        groups2 = sorted(filtered_financing[filtered_financing['KodeGrup2'].notna()]['KodeGrup2'].unique().tolist()) if 'KodeGrup2' in filtered_financing.columns else []
        groups_mapping2 = get_grup2_mapping()

        if groups2:
            # Calculate group totals for the latest date
            latest_date = filtered_financing['Tanggal'].max()
            group_data2 = filtered_financing[filtered_financing['Tanggal'] == latest_date].groupby('KodeGrup2')['Outstanding'].sum().reset_index()
            
            # Sort the data by Outstanding value in descending order and take top 20
            group_data2 = group_data2.sort_values('Outstanding', ascending=False)
            group_data_top20 = group_data2.head(20)  # Get top 20 groups
            
            # Calculate the sum of remaining groups
            others_sum = group_data2.iloc[20:]['Outstanding'].sum() if len(group_data2) > 20 else 0
            
            # Create bar chart data including "Others"
            x_values = [groups_mapping2.get(code, f"Group {code}") for code in group_data_top20['KodeGrup2']] + ['Others']
            y_values = list(group_data_top20['Outstanding'] / 1_000_000) + [others_sum / 1_000_000]

            text_values = [f"Rp {val/1_000_000:,.0f} Juta" for val in group_data_top20['Outstanding']] + [f"Rp {others_sum/1_000_000:,.0f} Juta"]
            
            # Create bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=x_values,
                y=y_values,
                text=text_values,
                textposition='auto',
                marker_color=['#1f77b4'] * 20 + ['#7f7f7f']  # Different color for "Others"
            ))
            
            fig.update_layout(
                title='Outstanding per Grup (Top 20 + Others)',
                xaxis_title='Grup',
                yaxis_title='Outstanding (Juta)',
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add detailed table (showing all groups)
            with st.expander("Tampilkan Rincian Data Grup Angsuran"):
                detailed_group2_data = pd.DataFrame({
                    'Grup Metode Angsuran': [groups_mapping2.get(code, f"Group {code}") for code in group_data2['KodeGrup2']],
                    'Outstanding': [f"Rp {val/1_000_000:,.0f} Juta" for val in group_data2['Outstanding']],
                    'Persentase': [(val/group_data2['Outstanding'].sum() * 100) for val in group_data2['Outstanding']]
                })
                detailed_group2_data['Persentase'] = detailed_group2_data['Persentase'].apply(lambda x: f"{x:.2f}%")
                
                # Add total row
                total_row_data = {
                    'Grup Metode Angsuran': 'Total Pembiayaan',
                    'Outstanding': f"Rp {group_data2['Outstanding'].sum()/1_000_000:,.0f} Juta",
                    'Persentase': '100.00%'
                }
                
                # Concatenate the original dataframe with the total row
                detailed_group2_data = pd.concat([
                    detailed_group2_data, 
                    pd.DataFrame([total_row_data])
                ], ignore_index=True)
                
                st.dataframe(detailed_group2_data, hide_index=True, use_container_width=True)
        else:
            st.info("Tidak ada data grup metode angsuran yang tersedia untuk periode yang dipilih.")

    # Collector Comparison Section
    with tab4:
        st.subheader(":material/support_agent: Perbandingan Antar Collector")
        

        # Get unique collectors from financing data and their mappings, excluding null values
        collectors = sorted(filtered_financing[filtered_financing['KdKolektor'].notna()]['KdKolektor'].unique().tolist()) if 'KdKolektor' in filtered_financing.columns else []
        
        if collectors:
            # Calculate collector totals for the latest date
            latest_date = filtered_financing['Tanggal'].max()
            collector_data = filtered_financing[filtered_financing['Tanggal'] == latest_date].groupby('KdKolektor')['Outstanding'].sum().reset_index()
            
            # Sort the data by Outstanding value in descending order and take top 20
            collector_data = collector_data.sort_values('Outstanding', ascending=False)
            collector_data_top20 = collector_data.head(20)  # Get top 20 collectors
            
            # Calculate the sum of remaining collectors
            others_sum = collector_data.iloc[20:]['Outstanding'].sum() if len(collector_data) > 20 else 0
            
            # Create bar chart data including "Others"
            x_values = list(collector_data_top20['KdKolektor']) + ['Others']
            y_values = list(collector_data_top20['Outstanding'] / 1_000_000) + [others_sum / 1_000_000]
            text_values = [f"Rp {val/1_000_000:,.0f} Juta" for val in collector_data_top20['Outstanding']] + [f"Rp {others_sum/1_000_000:,.0f} Juta"]
            
            # Create bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=x_values,
                y=y_values,
                text=text_values,
                textposition='auto',
                marker_color=['#1f77b4'] * 20 + ['#7f7f7f']  # Different color for "Others"
            ))
            
            fig.update_layout(
                title='Outstanding per Kolektor (Top 20 + Others)',
                xaxis_title='Kolektor',
                yaxis_title='Outstanding (Juta)',
                height=400,
                showlegend=False
            )

            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add detailed table (showing all collectors)
            with st.expander("Tampilkan Rincian Data Kolektor"):
                detailed_collector_data = pd.DataFrame({
                    'Kolektor': collector_data['KdKolektor'],
                    'Outstanding': [f"Rp {val/1_000_000:,.0f} Juta" for val in collector_data['Outstanding']],
                    'Persentase': [(val/collector_data['Outstanding'].sum() * 100) for val in collector_data['Outstanding']]
                })
                detailed_collector_data['Persentase'] = detailed_collector_data['Persentase'].apply(lambda x: f"{x:.2f}%")
                
                # Add total row
                total_row_data = {
                    'Kolektor': 'Total',
                    'Outstanding': f"Rp {collector_data['Outstanding'].sum()/1_000_000:,.0f} Juta",
                    'Persentase': '100.00%'
                }
                
                # Concatenate the original dataframe with the total row
                detailed_collector_data = pd.concat([
                    detailed_collector_data, 
                    pd.DataFrame([total_row_data])
                ], ignore_index=True)
                
                st.dataframe(detailed_collector_data, hide_index=True, use_container_width=True)
        else:
            st.info("Tidak ada data Kolektor yang tersedia untuk periode yang dipilih.")

    # Branch Comparison Section
    with tab5:

        st.subheader(":material/compare_arrows: Perbandingan Antar Cabang")
        

        # Branch selection
        col1, col2 = st.columns(2)
        with col1:
            branch1 = st.selectbox(
                "Cabang 1:",
                options=selected_items,
                format_func=lambda x: branches.get(x, x),
                key="lending_branch1"
            )
        with col2:
            branch2 = st.selectbox(
                "Cabang 2:",
                options=[x for x in selected_items if x != branch1],
                format_func=lambda x: branches.get(x, x),
                key="lending_branch2"
            )
        
        def get_branch_data(branch_code):
            """Calculate metrics for a specific branch"""
            branch_financing = filtered_financing[filtered_financing['KodeCabang'] == branch_code]
            branch_rahn = filtered_rahn[filtered_rahn['KodeCabang'] == branch_code]
            
            # Get initial and final values
            total_financing = int(branch_financing.groupby('Tanggal')['Outstanding'].sum().iloc[-1] / 1_000_000) if not branch_financing.empty else 0
            total_rahn = int(branch_rahn.groupby('Tanggal')['Nominal'].sum().iloc[-1] / 1_000_000) if not branch_rahn.empty else 0
            total_lending = total_financing + total_rahn
            
            total_financing_awal = int(branch_financing.groupby('Tanggal')['Outstanding'].sum().iloc[0] / 1_000_000) if not branch_financing.empty else 0
            total_rahn_awal = int(branch_rahn.groupby('Tanggal')['Nominal'].sum().iloc[0] / 1_000_000) if not branch_rahn.empty else 0
            total_lending_awal = total_financing_awal + total_rahn_awal
            
            # Get product breakdowns for latest date
            latest_date_financing = branch_financing['Tanggal'].max()
            latest_date_rahn = branch_rahn['Tanggal'].max()
            
            financing_by_product = branch_financing[branch_financing['Tanggal'] == latest_date_financing].groupby('KodeProduk')['Outstanding'].sum()
            rahn_by_product = branch_rahn[branch_rahn['Tanggal'] == latest_date_rahn].groupby('KodeProduk')['Nominal'].sum()
            
            return {
                'total_lending': total_lending,
                'total_financing': total_financing,
                'total_rahn': total_rahn,
                'total_lending_awal': total_lending_awal,
                'total_financing_awal': total_financing_awal,
                'total_rahn_awal': total_rahn_awal,
                'financing_by_product': financing_by_product,
                'rahn_by_product': rahn_by_product
            }
        
        # Get data for both branches
        branch1_data = get_branch_data(branch1)
        branch2_data = get_branch_data(branch2)
        
        # Display summary table
        summary_data = pd.DataFrame({
            'Metric': ['Total Lending', 'Total Pembiayaan', 'Total Rahn'],
            f'{branches.get(branch1, branch1)} Awal': [
                f"Rp {branch1_data['total_lending_awal']:,.0f} Juta",
                f"Rp {branch1_data['total_financing_awal']:,.0f} Juta",
                f"Rp {branch1_data['total_rahn_awal']:,.0f} Juta"
            ],
            f'{branches.get(branch1, branch1)} Akhir': [
                f"Rp {branch1_data['total_lending']:,.0f} Juta",
                f"Rp {branch1_data['total_financing']:,.0f} Juta",
                f"Rp {branch1_data['total_rahn']:,.0f} Juta"
            ],
            f'{branches.get(branch1, branch1)} Pertumbuhan': [
                f"Rp {(branch1_data['total_lending'] - branch1_data['total_lending_awal']):,.0f} Juta ({((branch1_data['total_lending'] - branch1_data['total_lending_awal'])/branch1_data['total_lending_awal']*100 if branch1_data['total_lending_awal'] != 0 else 0):,.1f}%)",
                f"Rp {(branch1_data['total_financing'] - branch1_data['total_financing_awal']):,.0f} Juta ({((branch1_data['total_financing'] - branch1_data['total_financing_awal'])/branch1_data['total_financing_awal']*100 if branch1_data['total_financing_awal'] != 0 else 0):,.1f}%)",
                f"Rp {(branch1_data['total_rahn'] - branch1_data['total_rahn_awal']):,.0f} Juta ({((branch1_data['total_rahn'] - branch1_data['total_rahn_awal'])/branch1_data['total_rahn_awal']*100 if branch1_data['total_rahn_awal'] != 0 else 0):,.1f}%)"
            ],
            f'{branches.get(branch2, branch2)} Awal': [
                f"Rp {branch2_data['total_lending_awal']:,.0f} Juta",
                f"Rp {branch2_data['total_financing_awal']:,.0f} Juta",
                f"Rp {branch2_data['total_rahn_awal']:,.0f} Juta"
            ],
            f'{branches.get(branch2, branch2)} Akhir': [
                f"Rp {branch2_data['total_lending']:,.0f} Juta",
                f"Rp {branch2_data['total_financing']:,.0f} Juta",
                f"Rp {branch2_data['total_rahn']:,.0f} Juta"
            ],
            f'{branches.get(branch2, branch2)} Pertumbuhan': [
                f"Rp {(branch2_data['total_lending'] - branch2_data['total_lending_awal']):,.0f} Juta ({((branch2_data['total_lending'] - branch2_data['total_lending_awal'])/branch2_data['total_lending_awal']*100 if branch2_data['total_lending_awal'] != 0 else 0):,.1f}%)",
                f"Rp {(branch2_data['total_financing'] - branch2_data['total_financing_awal']):,.0f} Juta ({((branch2_data['total_financing'] - branch2_data['total_financing_awal'])/branch2_data['total_financing_awal']*100 if branch2_data['total_financing_awal'] != 0 else 0):,.1f}%)",
                f"Rp {(branch2_data['total_rahn'] - branch2_data['total_rahn_awal']):,.0f} Juta ({((branch2_data['total_rahn'] - branch2_data['total_rahn_awal'])/branch2_data['total_rahn_awal']*100 if branch2_data['total_rahn_awal'] != 0 else 0):,.1f}%)"
            ]
        })
        st.dataframe(summary_data, hide_index=True, use_container_width=True)
        
        # Prepare product comparison data
        comparison_data = []
        
        # Add financing products
        for product in selected_financing_products:
            product_name = f"Pembiayaan - {financing_products.get(product, f'Product {product}')}"
            value1 = branch1_data['financing_by_product'].get(product, 0) / 1_000_000
            value2 = branch2_data['financing_by_product'].get(product, 0) / 1_000_000
            
            if value1 > 0 or value2 > 0:  # Only add if either branch has non-zero value
                comparison_data.append({
                    'Product': product_name,
                    '_akhir1': value1,  # Hidden columns for plotting
                    '_akhir2': value2
                })
        
        # Add rahn products
        for product in selected_rahn_products:
            product_name = f"Rahn - {rahn_products.get(product, f'Product {product}')}"
            value1 = branch1_data['rahn_by_product'].get(product, 0) / 1_000_000
            value2 = branch2_data['rahn_by_product'].get(product, 0) / 1_000_000
            
            if value1 > 0 or value2 > 0:  # Only add if either branch has non-zero value
                comparison_data.append({
                    'Product': product_name,
                    '_akhir1': value1,  # Hidden columns for plotting
                    '_akhir2': value2
                })
        
        # Add totals
        comparison_data.extend([
            {
                'Product': 'Total Pembiayaan',
                '_akhir1': branch1_data['total_financing'],
                '_akhir2': branch2_data['total_financing']
            },
            {
                'Product': 'Total Rahn',
                '_akhir1': branch1_data['total_rahn'],
                '_akhir2': branch2_data['total_rahn']
            },
            {
                'Product': 'Total Lending',
                '_akhir1': branch1_data['total_lending'],
                '_akhir2': branch2_data['total_lending']
            }
        ])
        
        # Create DataFrame
        comparison_df = pd.DataFrame(comparison_data)
        
        # Create and display bar chart
        st.markdown("##### Perbandingan Produk Lending per Cabang")
        fig = go.Figure()
        
        # Filter out totals for the chart
        product_data = comparison_df[~comparison_df['Product'].isin(['Total Pembiayaan', 'Total Rahn', 'Total Lending'])]
        
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

    # Update chart colors to match funding's implementation
    marker_colors = {
        'financing': '#1f77b4',  # Match funding's colors
        'rahn': '#f3e708',
        'total': '#f48322'
    }
