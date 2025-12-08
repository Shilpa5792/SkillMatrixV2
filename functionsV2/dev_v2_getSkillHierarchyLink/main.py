"""
Google Cloud Function that fetches rows from the SkillHierarchyLink table
with joined master tables (Domain, Discipline, Skill, Framework).
"""

import json
import os
from typing import Any, Dict, List

import psycopg2
from flask import Request
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

import db_utils


def fetch_skill_hierarchy_link() -> List[Dict[str, Any]]:
    """Fetch skill hierarchy links with joined master tables."""
    schema = os.getenv("DB_SCHEMA") or "public"
    
    # Build fully-qualified identifiers safely
    tbl_shl = sql.Identifier(schema, "SkillHierarchyLink")
    tbl_md = sql.Identifier(schema, "MasterDomain")
    tbl_mdisc = sql.Identifier(schema, "MasterDiscipline")
    tbl_ms = sql.Identifier(schema, "MasterSkill")
    tbl_mf = sql.Identifier(schema, "MasterFramework")
    
    query = sql.SQL("""
        SELECT 
            shl.id AS skillhierarchy_id,
            shl.domain_id,
            md.domain_name,
            shl.discipline_id,
            mdisc.discipline_name,
            shl.skill_id,
            ms.skill_name,
            shl.framework_id,
            mf.framework_name,
            mf.basic AS L1,
            mf.intermediate AS L2,
            mf.expert AS L3,
            shl.created_at,
            shl.updated_at
        FROM {shl} shl
        LEFT JOIN {md} md 
            ON md.id = shl.domain_id
        LEFT JOIN {mdisc} mdisc 
            ON mdisc.id = shl.discipline_id
        LEFT JOIN {ms} ms 
            ON ms.id = shl.skill_id
        LEFT JOIN {mf} mf 
            ON mf.id = shl.framework_id
        ORDER BY md.domain_name, mdisc.discipline_name, ms.skill_name, mf.framework_name
    """).format(
        shl=tbl_shl,
        md=tbl_md,
        mdisc=tbl_mdisc,
        ms=tbl_ms,
        mf=tbl_mf,
    )
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()


def dev_v2_get_skill_hierarchy_link(request: Request):
    """
    Cloud Function entry point for getting skill hierarchy links.
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
        data = fetch_skill_hierarchy_link()
        
        # Convert to JSON-serializable format
        results = []
        for row in data:
            result = dict(row)
            # Convert datetime objects to strings
            for key, value in result.items():
                if hasattr(value, 'isoformat'):
                    result[key] = value.isoformat()
            results.append(result)
        
        # Return as array (matching frontend expectation)
        return (json.dumps(results), 200, headers)
        
    except psycopg2.Error as exc:
        error_response = {"error": str(exc)}
        return (json.dumps(error_response), 500, headers)
    except Exception as exc:
        error_response = {"error": str(exc)}
        return (json.dumps(error_response), 500, headers)


"""
Deployment command (Production):

gcloud functions deploy get_skill_hierarchy_link \
  --runtime python310 \
  --trigger-http \
  --entry-point get_skill_hierarchy_link \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""

"""
Deployment command (Development):

gcloud functions deploy dev_v2_get_skill_hierarchy_link \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_skill_hierarchy_link \
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
    functions-framework --target=dev_v2_get_skill_hierarchy_link --source main.py --debug --port=8080

3. Test URL: http://127.0.0.1:8080/
"""

