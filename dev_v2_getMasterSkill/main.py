"""
Google Cloud Function that fetches rows from the MasterSkill table.
"""

import json
from typing import Any, Dict, List, Optional

import psycopg2
from flask import Request
from psycopg2.extras import RealDictCursor

import db_utils


def fetch_master_skill(search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch master skills from the database."""
    sql = """
        SELECT id, skill_name, description, "isMandatory", created_at, updated_at
        FROM "MasterSkill"
        WHERE (%(search)s IS NULL OR skill_name ILIKE %(pattern)s)
        ORDER BY updated_at DESC NULLS LAST
    """
    params = {"search": search, "pattern": f"%{search}%" if search else None}

    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def dev_v2_get_master_skill(request: Request):
    """
    Cloud Function entry point for getting master skills.
    
    Query parameters:
        search (optional): Case-insensitive skill_name filter
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
        # Get search parameter from query string
        search = request.args.get('search', None)
        
        # Fetch data from database
        data = fetch_master_skill(search=search)
        
        # Convert to JSON-serializable format
        results = []
        for row in data:
            result = dict(row)
            # Convert datetime objects to strings
            if 'created_at' in result and result['created_at']:
                result['created_at'] = result['created_at'].isoformat()
            if 'updated_at' in result and result['updated_at']:
                result['updated_at'] = result['updated_at'].isoformat()
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

gcloud functions deploy get_master_skill \
  --runtime python310 \
  --trigger-http \
  --entry-point get_master_skill \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""

"""
Deployment command (Development):

gcloud functions deploy dev_v2_get_master_skill \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_master_skill \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""

"""
Local testing command:

Then run:
    functions-framework --target=dev_v2_get_master_skill --source main.py --debug --port=8080

Test URL: http://127.0.0.1:8080/?search=python
"""

