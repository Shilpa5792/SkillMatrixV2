import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import settings

class Database:
    def __init__(self):
        # Quote the schema name to handle special characters like hyphens
        schema_name = settings.DB_SCHEMA.replace('"', '""')  # Escape any existing quotes
        
        self.connection_params = {
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'database': settings.DB_NAME,
            'user': settings.DB_USER,
            'password': settings.DB_PASS,
            'options': f'-c search_path="{schema_name}"'  # Quote schema name
        }
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                # Verify the schema is accessible
                cursor.execute("SELECT current_schema()")
                schema = cursor.fetchone()
                return {
                    "status": "success", 
                    "message": "Database connected successfully",
                    "current_schema": schema['current_schema'] if schema else None
                }
        except Exception as e:
            return {"status": "error", "message": f"Database connection failed: {str(e)}"}

db = Database()