import streamlit as st
import psycopg2
import snowflake.connector

def get_postgres_conn():
	return psycopg2.connect(
		host=st.secrets["postgres_host"],
		port=st.secrets["postgres_port"],
		dbname=st.secrets["postgres_dbname"],
		user=st.secrets["postgres_user"],
		password=st.secrets["postgres_password"]
	)

def get_snowflake_conn():
	return snowflake.connector.connect(
		user=st.secrets["sf_user"],
		password=st.secrets["sf_password"],
		account=st.secrets["sf_account"],
		warehouse=st.secrets["sf_warehouse"],
		database=st.secrets["sf_database"],
		schema=st.secrets["sf_schema"],
		role=st.secrets["sf_role"]
	)

def create_snowflake_sequence(sf_cur, table_name, start_value):
    seq_name = f"{table_name}_id_seq"
    sf_cur.execute(f"CREATE OR REPLACE SEQUENCE {seq_name} START WITH {start_value} INCREMENT BY 1")
    return seq_name

def migrate_table(table_name, columns):
    pg_conn = get_postgres_conn()
    pg_cur = pg_conn.cursor()
    sf_conn = get_snowflake_conn()
    sf_cur = sf_conn.cursor()

    # Get max id from Postgres
    pg_cur.execute(f"SELECT MAX(id) FROM {table_name}")
    max_id = pg_cur.fetchone()[0] or 0
    next_id = max_id + 1

    # Create sequence for id starting from next_id
    seq_name = create_snowflake_sequence(sf_cur, table_name, start_value=next_id)

    # Fetch all data from Postgres (excluding id)
    pg_cur.execute(f"SELECT {', '.join(columns[1:])} FROM {table_name}")
    rows = pg_cur.fetchall()

    # Delete all data in Snowflake target table
    sf_cur.execute(f"DELETE FROM {table_name}")

    # Insert data into Snowflake with sequence id
    if rows:
        for row in rows:
            row = list(row)
            # Special handling for expenses.receipt_blob
            if table_name == "expenses":
                idx = columns[1:].index("receipt_blob")
                val = row[idx]
                if isinstance(val, memoryview):
                    row[idx] = val.tobytes().hex()
                elif isinstance(val, bytes):
                    row[idx] = val.hex()
                elif val is None:
                    row[idx] = None
            sf_cur.execute(f"INSERT INTO {table_name} (id, {', '.join(columns[1:])}) VALUES ({seq_name}.NEXTVAL, {', '.join(['%s'] * len(columns[1:]))})", tuple(row))

    pg_cur.close()
    pg_conn.close()
    sf_cur.close()
    sf_conn.close()

if __name__ == "__main__":
	migrate_table("payment_details", ["id", "name", "amount", "date", "comments", "payment_type"])
	migrate_table("transfers", ["id", "name", "phone", "email"])
	migrate_table("sponsorship_items", ["id", "item", "amount", "sponsor_limit"])
	migrate_table("sponsors", ["id", "name", "email", "mobile", "apartment", "sponsorship", "donation", "gothram"])
	migrate_table("events", ["id", "title", "event_date", "event_time", "link", "description"])
	migrate_table("expenses", ["id", "category", "sub_category", "amount", "date", "spent_by", "comments", "receipt_path", "receipt_blob", "status", "created_at"])
	migrate_table("prasad_seva", ["id", "seva_type", "names", "item_name", "num_people", "apartment", "seva_date", "pooja_time", "created_by", "created_at", "status"])
	migrate_table("notification_emails", ["id", "email"])
