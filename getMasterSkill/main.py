"""
Simple script that reads DB credentials from a .env file and opens a
PostgreSQL connection so you can reuse the connection object elsewhere.
"""

import os
from contextlib import closing

from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql


def get_connection():
    """Create and return a psycopg2 connection using environment variables."""
    load_dotenv()

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dbname=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "5432")),
        options=f"-c search_path={os.getenv('DB_SCHEMA')}",
    )
    return conn


def fetch_table_preview(conn, table_name, limit=5):
    """Return row count and a small sample from the requested table."""
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {tbl}").format(tbl=sql.Identifier(table_name)))
        total_rows = cur.fetchone()[0]

        cur.execute(
            sql.SQL("SELECT * FROM {tbl} ORDER BY id DESC LIMIT %s").format(tbl=sql.Identifier(table_name)),
            (limit,),
        )
        sample_rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]

    return total_rows, col_names, sample_rows


def pretty_print_table(table_name, total_rows, col_names, sample_rows):
    print(f"\nTable: {table_name}")
    print(f"Total rows: {total_rows}")
    if not sample_rows:
        print("No data found.")
        return

    header = " | ".join(col_names)
    print(header)
    print("-" * len(header))
    for row in sample_rows:
        print(" | ".join(str(value) if value is not None else "NULL" for value in row))


def main():
    tables_to_check = [
       
        "MasterSkill",
     
    ]

    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_schema, version();")
            db_name, schema_name, version = cur.fetchone()
            print(f"Connected to {db_name}.{schema_name} -> {version}")

        for table in tables_to_check:
            total, cols, rows = fetch_table_preview(conn, table)
            pretty_print_table(table, total, cols, rows)


if __name__ == "__main__":
    main()

