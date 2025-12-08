"""
Cloud Function: Fetches all master skills from the new schema (SkillHierarchyLink).
Returns skills with domain_name, discipline_name, skill_name, framework_name, and level descriptions.
"""

import json
import os
from typing import List, Dict, Any

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from flask import Request

import db_utils


def fetch_master_skills() -> List[Dict[str, Any]]:
    """Fetch all master skills from SkillHierarchyLink with joined master tables."""
    schema = os.getenv("DB_SCHEMA") or "public"

    # Build fully-qualified identifiers safely
    tbl_shl = sql.Identifier(schema, "SkillHierarchyLink")
    tbl_md = sql.Identifier(schema, "MasterDomain")
    tbl_mdisc = sql.Identifier(schema, "MasterDiscipline")
    tbl_ms = sql.Identifier(schema, "MasterSkill")
    tbl_mf = sql.Identifier(schema, "MasterFramework")

    query = sql.SQL(
        """
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
        """
    ).format(
        shl=tbl_shl,
        md=tbl_md,
        mdisc=tbl_mdisc,
        ms=tbl_ms,
        mf=tbl_mf,
    )

    with db_utils.get_db_connection() as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()


def dev_v2_get_master_skills(request: Request):
    """
    Cloud Function entry point.
    Returns all master skills from the new schema.
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    try:
        rows = fetch_master_skills()

        # Convert datetime objects to ISO strings and generate hashId for compatibility
        import hashlib
        safe_rows = []
        for row in rows:
            safe_row = {}
            for key, val in row.items():
                if hasattr(val, "isoformat"):
                    safe_row[key] = val.isoformat()
                else:
                    safe_row[key] = val
            
            # Generate hashId from domain_name, discipline_name, skill_name, framework_name
            # This matches the frontend's hashId generation for matching skills
            domain = safe_row.get("domain_name") or ""
            discipline = safe_row.get("discipline_name") or ""
            skill = safe_row.get("skill_name") or ""
            framework = safe_row.get("framework_name") or ""
            hash_key = f"{domain}|{discipline}|{skill}|{framework}"
            hashId = hashlib.sha256(hash_key.encode("utf-8")).hexdigest()
            safe_row["hashId"] = hashId
            
            # Map to frontend expected format (Category, Sub-Category, etc.)
            safe_row["Category"] = safe_row.get("domain_name")
            safe_row["Sub-Category"] = safe_row.get("discipline_name")
            safe_row["Sub-Sub-Category"] = safe_row.get("skill_name")
            safe_row["Tools"] = safe_row.get("framework_name")
            
            safe_rows.append(safe_row)

        return (json.dumps(safe_rows), 200, headers)

    except psycopg2.Error as exc:
        return (json.dumps({"error": f"Database error: {str(exc)}"}), 500, headers)
    except Exception as exc:
        return (json.dumps({"error": str(exc)}), 500, headers)


"""
Deployment command (Production):

gcloud functions deploy get_master_skills \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_master_skills \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""

"""
Deployment command (Development):

gcloud functions deploy dev_v2_get_master_skills \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_master_skills \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""

"""
Local testing command:

Then run:
    functions-framework --target=dev_v2_get_master_skills --source main.py --debug --port=8080

Test URL: http://127.0.0.1:8080/
"""

