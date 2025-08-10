import psycopg2
import streamlit as st

# ---------- DB Connection ----------
def get_connection():
    return psycopg2.connect(
        host=st.secrets["postgres_host"],
        port=st.secrets["postgres_port"],
        dbname=st.secrets["postgres_dbname"],
        user=st.secrets["postgres_user"],
        password=st.secrets["postgres_password"]
    )

def create_payment_details_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_details (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            amount NUMERIC(10,2) NOT NULL,
            date DATE NOT NULL,
            comments TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

create_payment_details_table()

def create_transfers_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT
        )
    ''')
    conn.commit()

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sponsorship_items (
        id SERIAL PRIMARY KEY,
        item TEXT UNIQUE NOT NULL,
        amount NUMERIC NOT NULL,
        sponsor_limit INTEGER NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sponsors (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        mobile TEXT,
        apartment TEXT NOT NULL,
        sponsorship TEXT,
        donation NUMERIC DEFAULT 0
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        event_date DATE,
        event_time TIME,
        link TEXT,
        description TEXT
    );
    """)
    conn.commit()
