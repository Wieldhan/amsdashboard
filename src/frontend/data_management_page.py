import streamlit as st
import sqlite3
from datetime import datetime
from ..backend.database_lending import delete_financing_tables, get_financing_balance_data, delete_rahn_tables, get_rahn_balance_data
from ..backend.database_funding import (
    delete_deposito_tables, delete_saving_tables,
    get_deposito_balance_data, get_savings_balance_data
)

def get_table_info(db_path):
    """Get list of tables and their row counts from a database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    table_info = []
    for table in tables:
        table_name = table[0]
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        table_info.append((table_name, row_count))
    
    # Get total database size
    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    total_size_mb = round((page_count * page_size) / (1024 * 1024), 2)  # Convert to MB
    
    conn.close()
    return table_info, total_size_mb

def data_management_page():
    st.title("Data Management")
    
    # First row: Savings and Deposito
    st.subheader("Funding")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Savings Database")
        savings_tables, savings_size = get_table_info("./database/saving.db")
        
        st.write("Current Tables:")
        with st.expander("View Tables", expanded=True):
            # Filter for savings tables only
            savings_tables = [(table, count) for table, count in savings_tables if 'saving' in table.lower()]
            df_data = {
                'Table Name': [table for table, _ in savings_tables],
                'Rows': [count for _, count in savings_tables]
            }
            st.dataframe(
                df_data,
                column_config={
                    "Table Name": st.column_config.TextColumn("Table Name", width="medium"),
                    "Rows": st.column_config.NumberColumn("Rows", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        total_rows = sum(count for _, count in savings_tables)
        
        savings_info_col1, savings_info_col2 = st.columns(2)
        with savings_info_col1:
            st.write(f"Total Rows: {total_rows:,}")
        with savings_info_col2:
            st.write(f"Data Size: {savings_size:.2f} MB")
        
        # Add date inputs for savings sync
        savings_col1, savings_col2 = st.columns(2)
        with savings_col1:
            st.write("Start Date: 2020-01-01")
            savings_start_date = datetime(2020, 1, 1)
        with savings_col2:
            current_date = datetime.now().strftime('%Y-%m-%d')
            st.write(f"End Date: {current_date}")
            savings_end_date = datetime.now()
            
        # Actions for Savings DB
        st.write("Actions:")
        
        col4_1, col4_2 = st.columns(2)
        
        with col4_1:
            if st.button("🔄 Sync from SQL Server", key="sync_savings"):
                if savings_start_date > savings_end_date:
                    st.error("Start date must be before end date!")
                else:
                    with st.spinner("Syncing Savings data..."):
                        try:
                            get_savings_balance_data(savings_start_date, savings_end_date)
                            st.success("Successfully synced Savings data!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error syncing data: {str(e)}")
        
        with col4_2:
            if st.button("🗑️ Clear All Data", key="clear_savings"):
                if st.session_state.get('confirm_delete_savings', False):
                    try:
                        delete_saving_tables()
                        st.success("Successfully cleared Savings database!")
                        st.session_state.confirm_delete_savings = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {str(e)}")
                else:
                    st.warning("⚠️ Are you sure? Click again to confirm deletion.")
                    st.session_state.confirm_delete_savings = True

    with col2:
        st.markdown("### Deposito Database")
        deposito_tables, deposito_size = get_table_info("./database/deposito.db")
        
        st.write("Current Tables:")
        with st.expander("View Tables", expanded=True):
            # Filter for deposito tables only
            deposito_tables = [(table, count) for table, count in deposito_tables if 'deposito' in table.lower()]
            df_data = {
                'Table Name': [table for table, _ in deposito_tables],
                'Rows': [count for _, count in deposito_tables]
            }
            st.dataframe(
                df_data,
                column_config={
                    "Table Name": st.column_config.TextColumn("Table Name", width="medium"),
                    "Rows": st.column_config.NumberColumn("Rows", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        total_rows = sum(count for _, count in deposito_tables)
        
        deposito_info_col1, deposito_info_col2 = st.columns(2)
        with deposito_info_col1:
            st.write(f"Total Rows: {total_rows:,}")
        with deposito_info_col2:
            st.write(f"Data Size: {deposito_size:.2f} MB")
        
        # Add date inputs for deposito sync
        deposito_col1, deposito_col2 = st.columns(2)
        with deposito_col1:
            st.write("Start Date: 2020-01-01")
            deposito_start_date = datetime(2020, 1, 1)
        with deposito_col2:
            current_date = datetime.now().strftime('%Y-%m-%d')
            st.write(f"End Date: {current_date}")
            deposito_end_date = datetime.now()
            
        # Actions for Deposito DB
        st.write("Actions:")
        
        col3_1, col3_2 = st.columns(2)
        
        with col3_1:
            if st.button("🔄 Sync from SQL Server", key="sync_deposito"):
                if deposito_start_date > deposito_end_date:
                    st.error("Start date must be before end date!")
                else:
                    with st.spinner("Syncing Deposito data..."):
                        try:
                            get_deposito_balance_data(deposito_start_date, deposito_end_date)
                            st.success("Successfully synced Deposito data!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error syncing data: {str(e)}")
        
        with col3_2:
            if st.button("🗑️ Clear All Data", key="clear_deposito"):
                if st.session_state.get('confirm_delete_deposito', False):
                    try:
                        delete_deposito_tables()
                        st.success("Successfully cleared Deposito database!")
                        st.session_state.confirm_delete_deposito = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {str(e)}")
                else:
                    st.warning("⚠️ Are you sure? Click again to confirm deletion.")
                    st.session_state.confirm_delete_deposito = True

    # Add a divider between rows
    st.divider()
    
    # Second row: Financing and Rahn
    st.subheader("Lending")
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### Financing Database")
        financing_tables, financing_size = get_table_info("./database/financing.db")
        
        st.write("Current Tables:")
        with st.expander("View Tables", expanded=True):
            # Convert table info to a format suitable for dataframe
            df_data = {
                'Table Name': [table for table, _ in financing_tables],
                'Rows': [count for _, count in financing_tables]
            }
            
            st.dataframe(
                df_data,
                column_config={
                    "Table Name": st.column_config.TextColumn("Table Name", width="medium"),
                    "Rows": st.column_config.NumberColumn("Rows", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        total_rows = sum(count for _, count in financing_tables)
        
        financing_info_col1, financing_info_col2 = st.columns(2)
        with financing_info_col1:
            st.write(f"Total Rows: {total_rows:,}")
        with financing_info_col2:
            st.write(f"Data Size: {financing_size:.2f} MB")
        
        # Add date inputs for financing sync
        fin_col1, fin_col2 = st.columns(2)
        with fin_col1:
            st.write("Start Date: 2020-01-01")
            financing_start_date = datetime(2020, 1, 1)
        with fin_col2:
            current_date = datetime.now().strftime('%Y-%m-%d')
            st.write(f"End Date: {current_date}")
            financing_end_date = datetime.now()
        
        # Actions for Financing DB
        st.write("Actions:")
       
        col1_1, col1_2 = st.columns(2)
        
        with col1_1:
            if st.button("🔄 Sync from SQL Server", key="sync_financing"):
                if financing_start_date > financing_end_date:
                    st.error("Start date must be before end date!")
                else:
                    with st.spinner("Syncing Financing data..."):
                        try:
                            get_financing_balance_data(financing_start_date, financing_end_date)
                            st.success("Successfully synced Financing data!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error syncing data: {str(e)}")
        
        with col1_2:
            if st.button("🗑️ Clear All Data", key="clear_financing"):
                if st.session_state.get('confirm_delete_financing', False):
                    try:
                        delete_financing_tables()
                        st.success("Successfully cleared Financing database!")
                        st.session_state.confirm_delete_financing = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {str(e)}")
                else:
                    st.warning("⚠️ Are you sure? Click again to confirm deletion.")
                    st.session_state.confirm_delete_financing = True
    
    with col4:
        st.markdown("### Rahn Database")
        rahn_tables, rahn_size = get_table_info("./database/rahn.db")
        
        st.write("Current Tables:")
        with st.expander("View Tables", expanded=True):
            df_data = {
                'Table Name': [table for table, _ in rahn_tables],
                'Rows': [count for _, count in rahn_tables]
            }
            st.dataframe(
                df_data,
                column_config={
                    "Table Name": st.column_config.TextColumn("Table Name", width="medium"),
                    "Rows": st.column_config.NumberColumn("Rows", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        total_rows = sum(count for _, count in rahn_tables)
        
        rahn_info_col1, rahn_info_col2 = st.columns(2)
        with rahn_info_col1:
            st.write(f"Total Rows: {total_rows:,}")
        with rahn_info_col2:
            st.write(f"Data Size: {rahn_size:.2f} MB")
        
        # Add date inputs for rahn sync
        rahn_col1, rahn_col2 = st.columns(2)
        with rahn_col1:
            st.write("Start Date: 2020-01-01")
            rahn_start_date = datetime(2020, 1, 1)
        with rahn_col2:
            current_date = datetime.now().strftime('%Y-%m-%d')
            st.write(f"End Date: {current_date}")
            rahn_end_date = datetime.now()
            
        # Actions for Rahn DB
        st.write("Actions:")
        
        col4_1, col4_2 = st.columns(2)
        
        with col4_1:
            if st.button("🔄 Sync from SQL Server", key="sync_rahn"):
                if rahn_start_date > rahn_end_date:
                    st.error("Start date must be before end date!")
                else:
                    with st.spinner("Syncing Rahn data..."):
                        try:
                            get_rahn_balance_data(rahn_start_date, rahn_end_date)
                            st.success("Successfully synced Rahn data!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error syncing data: {str(e)}")
        
        with col4_2:
            if st.button("🗑️ Clear All Data", key="clear_rahn"):
                if st.session_state.get('confirm_delete_rahn', False):
                    try:
                        delete_rahn_tables()
                        st.success("Successfully cleared Rahn database!")
                        st.session_state.confirm_delete_rahn = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {str(e)}")
                else:
                    st.warning("⚠️ Are you sure? Click again to confirm deletion.")
                    st.session_state.confirm_delete_rahn = True

    # Add timestamp of last sync
    st.divider()
    st.caption(f"Last page refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
