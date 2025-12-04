"""
Google Cloud Function that fetches rows from the MasterDomain table.
"""

import json
from typing import Any, Dict, List

import psycopg2
from flask import Request
from psycopg2.extras import RealDictCursor

import db_utils


def fetch_master_domain() -> List[Dict[str, Any]]:
    """Fetch master domains from the database."""
    sql = 'SELECT * FROM "MasterDomain" ORDER BY id'
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


def dev_v2_get_master_domain(request: Request):
    """
    Cloud Function entry point for getting master domains.
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Set CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    try:
        # Fetch data from database
        data = fetch_master_domain()
        
        # Convert to JSON-serializable format
        results = []
        for row in data:
            result = dict(row)
            # Convert datetime objects to strings
            for key, value in result.items():
                if hasattr(value, 'isoformat'):
                    result[key] = value.isoformat()
            results.append(result)
        
        response_data = {"count": len(results), "results": results}
        return (json.dumps(response_data), 200, headers)
        
    except psycopg2.Error as exc:
        error_response = {"error": str(exc)}
        return (json.dumps(error_response), 500, headers)
    except Exception as exc:
        error_response = {"error": str(exc)}
        return (json.dumps(error_response), 500, headers)


"""
Deployment command (Production):

gcloud functions deploy get_master_domain \
  --runtime python310 \
  --trigger-http \
  --entry-point get_master_domain \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""

"""
Deployment command (Development):

gcloud functions deploy dev_v2_get_master_domain \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_master_domain \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""

"""
Local testing command:

1. Create a .env file in this directory with your database credentials:
   DB_HOST=your-database-host
   DB_USER=your-database-username
   DB_PASS=your-database-password
   DB_NAME=your-database-name
   DB_PORT=5432
   DB_SCHEMA=your-schema-name

2. Then run:
    functions-framework --target=dev_v2_get_master_domain --source main.py --debug --port=8080

3. Test URL: http://127.0.0.1:8080/ (NOT http://127.0.0.1:8080/dev_v2_get_master_domain)
"""

