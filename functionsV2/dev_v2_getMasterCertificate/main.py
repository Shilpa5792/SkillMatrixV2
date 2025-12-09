"""
Google Cloud Function that fetches master certificates with provider information.
Joins data from MasterCertificateProvider, ProviderCertificateMapping, and MasterCertificate tables.
"""
 
import json
from typing import Any, Dict, List
 
import psycopg2
from flask import Request
from psycopg2.extras import RealDictCursor
 
import db_utils
 
def fetch_master_certificate() -> List[Dict[str, Any]]:
    """
    Fetch master certificates with provider information from the database.
    
    Returns a list of certificates with their provider details by joining:
    - MasterCertificateProvider (providers)
    - ProviderCertificateMapping (mappings)
    - MasterCertificate (certificates)
    """
    sql = """
        SELECT 
            pcm.id,
            mcp.id as provider_id,
            mcp.certprovider,
            mc.id as certificate_id,
            mc.certname,
            mc.certlevel,
            mc.validyears,
            mc.isactive,
            pcm.created_at,
            pcm.updated_at
        FROM "ProviderCertificateMapping" pcm
        JOIN "MasterCertificateProvider" mcp ON pcm.provider_id = mcp.id
        JOIN "MasterCertificate" mc ON pcm.certificate_id = mc.id
        ORDER BY mcp.certprovider, mc.certlevel, mc.certname
    """
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()

def fetch_providers() -> List[Dict[str, Any]]:
    """Fetch all certification providers."""
    sql = 'SELECT * FROM "MasterCertificateProvider" ORDER BY certprovider'
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()

def fetch_certificates() -> List[Dict[str, Any]]:
    """Fetch all certificates (without provider info)."""
    sql = 'SELECT * FROM "MasterCertificate" ORDER BY certlevel, certname'
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()

def dev_v2_get_master_certificate(request: Request):
    """
    Cloud Function entry point for getting master certificates.
    
    Query Parameters:
    - view: 'full' (default) - Returns certificates with provider info (JOIN)
    - view: 'providers' - Returns only providers
    - view: 'certificates' - Returns only certificates (no provider info)
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
        # Get view parameter (default: 'full')
        view = request.args.get('view', 'full')
        
        # Fetch data based on view parameter
        if view == 'providers':
            data = fetch_providers()
        elif view == 'certificates':
            data = fetch_certificates()
        else:  # default: 'full'
            data = fetch_master_certificate()
       
        # Convert to JSON-serializable format
        results = []
        for row in data:
            result = dict(row)
            # Convert datetime objects to strings
            for key, value in result.items():
                if hasattr(value, 'isoformat'):
                    result[key] = value.isoformat()
            results.append(result)
       
        response_data = {
            "count": len(results), 
            "view": view,
            "results": results
        }
        return (json.dumps(response_data), 200, headers)
       
    except psycopg2.Error as exc:
        error_response = {
            "error": "Database error",
            "details": str(exc)
        }
        return (json.dumps(error_response), 500, headers)
    except Exception as exc:
        error_response = {
            "error": "Internal server error",
            "details": str(exc)
        }
        return (json.dumps(error_response), 500, headers)
 
"""
Deployment command (Production):
 
gcloud functions deploy get_master_certificate \
  --runtime python310 \
  --trigger-http \
  --entry-point get_master_certificate \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""
 
"""
Deployment command (Development):
 
gcloud functions deploy dev_v2_get_master_certificate \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_master_certificate \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""
 
"""
Local testing command:
 
Then run:
    functions-framework --target=dev_v2_get_master_certificate --source main.py --debug --port=8080
 
Test URLs:
    Full view (with provider): http://127.0.0.1:8080/
    Full view explicit: http://127.0.0.1:8080/?view=full
    Providers only: http://127.0.0.1:8080/?view=providers
    Certificates only: http://127.0.0.1:8080/?view=certificates
"""