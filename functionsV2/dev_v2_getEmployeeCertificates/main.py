"""
Google Cloud Function that fetches employee certificates.
Uses JOINs to validate mapping relationships but returns only EmployeeCertificates table structure.
"""

import json
from typing import Any, Dict, List

import psycopg2
from flask import Request
from psycopg2.extras import RealDictCursor

import db_utils


def fetch_employee_certificate() -> List[Dict[str, Any]]:
    """
    Fetch employee certificates with full JOIN to validate mappings,
    but return only EmployeeCertificates table columns.
    """
    sql = """
        SELECT 
            ec.id,
            ec.employee_id,
            ec.certificate_id,
            ec.issued_date,
            ec.expiry_date,
            ec.created_at,
            ec.updated_at
        FROM "EmployeeCertificates" ec
        JOIN "ProviderCertificateMapping" pcm ON ec.certificate_id::integer = pcm.id
        JOIN "MasterCertificate" mc ON pcm.certificate_id = mc.id
        JOIN "MasterCertificateProvider" mcp ON pcm.provider_id = mcp.id
        ORDER BY ec.id
    """
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


def dev_v2_get_employee_certificate(request: Request):
    """
    Cloud Function entry point for getting employee certificates.
    
    Query Parameters:
    - employee_id: Filter by specific employee ID (optional)
    
    Returns:
    EmployeeCertificates table data where certificate_id references ProviderCertificateMapping.id
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
        data = fetch_employee_certificate()
        
        # Optional: Filter by employee_id if provided
        employee_id = request.args.get('employee_id')
        if employee_id:
            data = [row for row in data if row.get('employee_id') == int(employee_id)]
        
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

gcloud functions deploy get_employee_certificate \
  --runtime python310 \
  --trigger-http \
  --entry-point get_employee_certificate \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""

"""
Deployment command (Development):

gcloud functions deploy dev_v2_get_employee_certificate \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_employee_certificate \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""

"""
Local testing command:

Then run:
    functions-framework --target=dev_v2_get_employee_certificate --source main.py --debug --port=8080

Test URLs:
    All employee certificates: http://127.0.0.1:8080/
    Specific employee: http://127.0.0.1:8080/?employee_id=4

Response format (EmployeeCertificates table structure):
{
  "count": 2,
  "results": [
    {
      "id": 11,
      "employee_id": 4,
      "certificate_id": 1,  // References ProviderCertificateMapping.id
      "issued_date": "2024-01-15T00:00:00",
      "expiry_date": "2027-01-15T00:00:00",
      "created_at": "2025-12-09T10:11:05.820548",
      "updated_at": "2025-12-09T10:11:05.820548"
    }
  ]
}

Future mapping in application:
- Use certificate_id to JOIN with ProviderCertificateMapping
- ProviderCertificateMapping has provider_id and certificate_id (master)
- This allows mapping to MasterCertificate and MasterCertificateProvider
"""