"""
Shared database utility module for cloud functions.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dbname=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "5432")),
        options=f"-c search_path={os.getenv('DB_SCHEMA')}",
    )
    return conn

