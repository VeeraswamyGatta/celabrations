import psycopg2
import streamlit as st
import snowflake.connector

_switch_db_type = st.secrets.get("db_type", "postgres")

# ---------- DB Connection ----------
def get_connection(switch_db_type=None):
    db_type = switch_db_type if switch_db_type is not None else _switch_db_type
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
            schema=st.secrets["sf_schema"]
        )
    else:
        raise ValueError(f"Unsupported DB type: {db_type}")

def create_payment_details_table():
    conn = get_connection()
    cursor = conn.cursor()
    db_type = _switch_db_type
    if db_type == "snowflake":
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_details (
                    id INTEGER AUTOINCREMENT PRIMARY KEY,
                    name TEXT NOT NULL,
                    amount NUMERIC(10,2) NOT NULL,
                    date DATE NOT NULL,
                    comments TEXT,
                    payment_type TEXT
                )
            ''')
    else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_details (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    amount NUMERIC(10,2) NOT NULL,
                    date DATE NOT NULL,
                    comments TEXT,
                    payment_type TEXT
                )
            ''')
    conn.commit()
    cursor.close()
    conn.close()

create_payment_details_table()

def create_transfers_table(conn):
    cursor = conn.cursor()
    db_type = _switch_db_type
    if db_type == "snowflake":
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER AUTOINCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT
            )
        ''')
    else:
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
    db_type = _switch_db_type
    if db_type == "snowflake":
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sponsorship_items (
            id INTEGER AUTOINCREMENT PRIMARY KEY,
            item TEXT UNIQUE NOT NULL,
            amount NUMERIC NOT NULL,
            sponsor_limit INTEGER NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sponsors (
            id INTEGER AUTOINCREMENT PRIMARY KEY,
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
            id INTEGER AUTOINCREMENT PRIMARY KEY,
            title TEXT NOT NULL,
            event_date DATE,
            event_time TIME,
            link TEXT,
            description TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_emails (
            id INTEGER AUTOINCREMENT PRIMARY KEY,
            email TEXT NOT NULL
        );
        """)
    else:
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
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_emails (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL
        );
        """)
    conn.commit()
