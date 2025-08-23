import psycopg2
import snowflake.connector
import pandas as pd
import streamlit as st
import datetime

def get_pg_config():
    return {
        'host': st.secrets["postgres_host"],
        'port': st.secrets["postgres_port"],
        'dbname': st.secrets["postgres_dbname"],
        'user': st.secrets["postgres_user"],
        'password': st.secrets["postgres_password"]
    }

def get_sf_config():
    return {
        'user': st.secrets["sf_user"],
        'password': st.secrets["sf_password"],
        'account': st.secrets["sf_account"],
        'warehouse': st.secrets["sf_warehouse"],
        'database': st.secrets["sf_database"],
        'schema': st.secrets["sf_schema"]
    }

def map_pg_to_sf_type(pg_type):
    type_map = {
        'integer': 'NUMBER',
        'bigint': 'NUMBER',
        'smallint': 'NUMBER',
        'text': 'STRING',
        'character varying': 'STRING',
        'timestamp without time zone': 'TIMESTAMP',
        'date': 'DATE',
        'boolean': 'BOOLEAN',
    }
    return type_map.get(pg_type, 'STRING')

def main():
    # Read credentials from Streamlit secrets
    PG_CONFIG = get_pg_config()
    SF_CONFIG = get_sf_config()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()

    # Connect to Snowflake
    sf_conn = snowflake.connector.connect(**SF_CONFIG)
    sf_cursor = sf_conn.cursor()

    # Drop schema in Snowflake (will drop all tables)
    sf_cursor.execute(f"DROP SCHEMA IF EXISTS {SF_CONFIG['schema']} CASCADE;")
    sf_cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {SF_CONFIG['schema']};")
    sf_cursor.execute(f"USE SCHEMA {SF_CONFIG['schema']};")

    # Get all table names from PostgreSQL
    pg_cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    tables = [row[0] for row in pg_cursor.fetchall()]

    for table in tables:
        # Get table schema from PostgreSQL
        pg_cursor.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{table}';
        """)
        columns = pg_cursor.fetchall()
        col_defs = []
        for col_name, col_type in columns:
            sf_type = map_pg_to_sf_type(col_type)
            col_defs.append(f'"{col_name}" {sf_type}')
        create_stmt = f'CREATE OR REPLACE TABLE "{table}" ({", ".join(col_defs)});'
        sf_cursor.execute(create_stmt)

        # Fetch data from PostgreSQL
        df = pd.read_sql(f'SELECT * FROM "{table}"', pg_conn)
        # Insert data into Snowflake
        # Get Snowflake table column order
        sf_cursor.execute(f"SHOW COLUMNS IN {SF_CONFIG['database']}.{SF_CONFIG['schema']}.\"{table}\"")
        sf_columns = [row[2] for row in sf_cursor.fetchall()]
        # Reorder DataFrame columns to match Snowflake
        df = df[sf_columns]
        col_names = df.columns.tolist()
        for _, row in df.iterrows():
            values = []
            for val in row:
                if pd.isnull(val):
                    values.append('NULL')
                elif isinstance(val, str):
                    values.append("'{}'".format(val.replace("'", "''")))
                elif isinstance(val, (pd.Timestamp, pd.DatetimeIndex)):
                    values.append("'{}'".format(val.strftime('%Y-%m-%d %H:%M:%S')))
                elif isinstance(val, (datetime.date, datetime.datetime)):
                    values.append("'{}'".format(val.isoformat()))
                elif hasattr(val, 'isoformat'):
                    values.append("'{}'".format(val.isoformat()))
                elif isinstance(val, (pd.Timedelta, pd.TimedeltaIndex)):
                    values.append("'{}'".format(str(val)))
                else:
                    values.append(str(val))
            col_names_sql = ', '.join(['"{}"'.format(c) for c in col_names])
            insert_stmt = f'INSERT INTO "{table}" ({col_names_sql}) VALUES ({", ".join(values)});'
            print(insert_stmt)
            insert_stmt = f'INSERT INTO "{table}" VALUES ({", ".join(values)});'
            sf_cursor.execute(insert_stmt)

    pg_cursor.close()
    pg_conn.close()
    sf_cursor.close()
    sf_conn.close()

if __name__ == "__main__":
    main()
