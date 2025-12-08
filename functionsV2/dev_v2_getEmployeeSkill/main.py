"""
Cloud Function: accepts JSON body with email and returns skill hierarchy rows.
"""

import json
import os
from typing import List, Dict

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from flask import Request

import db_utils


def fetch_skills_for_email(email: str) -> List[Dict[str, str]]:
    """Run the provided query to fetch skill hierarchy data for an email."""
    schema = os.getenv("DB_SCHEMA") or "public"

    # Build fully-qualified identifiers safely
    tbl_shl = sql.Identifier(schema, "SkillHierarchyLink")
    tbl_es = sql.Identifier(schema, "EmployeeSkill")
    tbl_e = sql.Identifier(schema, "Employee")
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
            es.levelselected,               -- ⭐ Use lowercase column name
            shl.created_at,
            shl.updated_at
        FROM {shl} shl
        JOIN {es} es 
            ON es.skillhierarchy_id = shl.id
        JOIN {e} e 
            ON e.id = es.employee_id
        LEFT JOIN {md} md 
            ON md.id = shl.domain_id
        LEFT JOIN {mdisc} mdisc 
            ON mdisc.id = shl.discipline_id
        LEFT JOIN {ms} ms 
            ON ms.id = shl.skill_id
        LEFT JOIN {mf} mf 
            ON mf.id = shl.framework_id
        WHERE LOWER(e.email) = LOWER(%s)
        """
    ).format(
        shl=tbl_shl,
        es=tbl_es,
        e=tbl_e,
        md=tbl_md,
        mdisc=tbl_mdisc,
        ms=tbl_ms,
        mf=tbl_mf,
    )

    with db_utils.get_db_connection() as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (email,))
            return cur.fetchall()

def dev_v2_get_employee_skill(request: Request):
    """
    Cloud Function entry point.
    Accepts POST/GET with email and returns skill hierarchy rows.
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    try:
        # Extract email
        email = None
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            email = data.get("email")
        elif request.method == "GET":
            email = request.args.get("email")

        if not email:
            return (json.dumps({"error": "Missing required field: email"}), 400, headers)

        email = str(email).strip()

        rows = fetch_skills_for_email(email)

        # Convert datetime objects to ISO strings for JSON serialization
        safe_rows = []
        for row in rows:
            safe_row = {}
            for key, val in row.items():
                if hasattr(val, "isoformat"):
                    safe_row[key] = val.isoformat()
                else:
                    safe_row[key] = val
            safe_rows.append(safe_row)

        return (json.dumps({"email": email.lower(), "skills": safe_rows}), 200, headers)

    except psycopg2.Error as exc:
        return (json.dumps({"error": f"Database error: {str(exc)}"}), 500, headers)
    except Exception as exc:
        return (json.dumps({"error": str(exc)}), 500, headers)


"""
Deployment command (Production):

gcloud functions deploy get_employee_skill \
  --runtime python310 \
  --trigger-http \
  --entry-point get_employee_skill \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""

"""
Deployment command (Development):

gcloud functions deploy dev_v2_get_employee_skill \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_employee_skill \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""

"""
Local testing command:

Then run:
    functions-framework --target=dev_v2_get_employee_skill --source main.py --debug --port=8080

Test URL: http://127.0.0.1:8080/
"""

