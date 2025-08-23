
import psycopg2
import streamlit as st
import snowflake.connector

# ---------- DB Connection ----------
def get_connection():
    db_type = st.secrets.get("db_type", "postgres").lower()
    if db_type == "postgres":
        return psycopg2.connect(
            host=st.secrets["postgres_host"],
            port=st.secrets["postgres_port"],
            dbname=st.secrets["postgres_dbname"],
            user=st.secrets["postgres_user"],
            password=st.secrets["postgres_password"]
        )
    elif db_type == "snowflake":
        return snowflake.connector.connect(
            user=st.secrets["sf_user"],
            password=st.secrets["sf_password"],
            account=st.secrets["sf_account"],
            warehouse=st.secrets["sf_warehouse"],
            database=st.secrets["sf_database"],
            schema=st.secrets["sf_schema"],
            role=st.secrets["sf_role"]
        )
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

