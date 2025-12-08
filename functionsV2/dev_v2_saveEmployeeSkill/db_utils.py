"""
Shared database utility module for cloud functions.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    # Get required environment variables
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")
    db_port = os.getenv("DB_PORT", "5432")
    db_schema = os.getenv("DB_SCHEMA")
    
    # Validate required environment variables
    missing_vars = []
    if not db_host:
        missing_vars.append("DB_HOST")
    if not db_user:
        missing_vars.append("DB_USER")
    if not db_pass:
        missing_vars.append("DB_PASS")
    if not db_name:
        missing_vars.append("DB_NAME")
    
    if missing_vars:
        raise ValueError(
            f"Missing required database environment variables: {', '.join(missing_vars)}. "
            f"Please set these in the Cloud Function environment variables."
        )
    
    # Build connection parameters
    conn_params = {
        "host": db_host,
        "user": db_user,
        "password": db_pass,
        "dbname": db_name,
        "port": int(db_port),
    }
    
    # Add schema if provided
    if db_schema:
        conn_params["options"] = f"-c search_path={db_schema}"
    
    try:
        conn = psycopg2.connect(**conn_params)
        return conn
    except psycopg2.Error as e:
        raise ConnectionError(
            f"Failed to connect to database: {str(e)}. "
            f"Check DB_HOST={db_host}, DB_NAME={db_name}, DB_PORT={db_port}"
        ) from e

