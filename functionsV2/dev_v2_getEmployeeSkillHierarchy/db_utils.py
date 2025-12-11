"""
Shared database utility module for cloud functions.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    # Get schema name and quote it to handle special characters like hyphens
    schema_name = os.getenv('DB_SCHEMA', 'public')
    # Escape any existing quotes in schema name
    schema_name = schema_name.replace('"', '""')
    
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dbname=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "5432")),
        options=f'-c search_path="{schema_name}"',  # Quote the schema name
    )
    return conn