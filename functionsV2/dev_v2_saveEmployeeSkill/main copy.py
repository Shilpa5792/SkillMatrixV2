"""
Cloud Function: Saves employee skills to EmployeeSkill table using skillhierarchy_id.
Accepts JSON body with email and skills array (with hashId and Level).
"""

import json
import os
import logging
from typing import List, Dict, Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from flask import Request

import  db_utils

logger = logging.getLogger(__name__)


# Note: hashId lookup removed - we now use skillhierarchy_id directly


def get_employee_id(email: str, conn) -> Optional[int]:
    """Get employee ID from email."""
    schema = os.getenv("DB_SCHEMA") or "public"
    query = sql.SQL('SELECT id FROM {employee} WHERE LOWER(email) = LOWER(%s)').format(
        employee=sql.Identifier(schema, "Employee")
    )
    
    with conn.cursor() as cur:
        cur.execute(query, (email,))
        result = cur.fetchone()
        return result[0] if result else None


def save_employee_skills_v2(email: str, skills: List[Dict], manager_email: str = "") -> Dict:
    """
    Save employee skills to EmployeeSkill table.
    Skills should have: hashId (or skillhierarchy_id) and Level.
    """
    schema = os.getenv("DB_SCHEMA") or "public"
    
    with db_utils.get_db_connection() as conn:
        conn.autocommit = False
        
        try:
            # Get employee ID
            emp_id = get_employee_id(email, conn)
            if not emp_id:
                raise ValueError(f"Employee not found for email: {email}")
            
            # Update manager email if provided
            if manager_email:
                update_mgr_query = sql.SQL("""
                    UPDATE {employee} 
                    SET "managerEmail" = %s 
                    WHERE id = %s AND ("managerEmail" IS NULL OR "managerEmail" = '')
                """).format(employee=sql.Identifier(schema, "Employee"))
                with conn.cursor() as cur:
                    cur.execute(update_mgr_query, (manager_email.lower(), emp_id))
            
            # Get existing skills for this employee
            existing_query = sql.SQL("""
                SELECT "skillhierarchy_id", "levelSelected", "approvalStatus", "approvedByEmail"
                FROM {employee_skill}
                WHERE "employee_id" = %s
            """).format(employee_skill=sql.Identifier(schema, "EmployeeSkill"))
            
            existing_skills = {}
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(existing_query, (emp_id,))
                for row in cur.fetchall():
                    existing_skills[row["skillhierarchy_id"]] = {
                        "levelSelected": row["levelSelected"],
                        "approvalStatus": row["approvalStatus"],
                        "approvedByEmail": row["approvedByEmail"],
                    }
            
            # Process skills and map hashId to skillhierarchy_id
            skill_rows = []
            pending_skills = []
            skillhierarchy_ids_to_save = []
            
            for sk in skills:
                skillhierarchy_id = sk.get("skillhierarchy_id")
                level = sk.get("Level")
                
                if not level or not skillhierarchy_id:
                    logger.warning(f"Missing skillhierarchy_id or Level in skill: {sk}")
                    continue
                
                # Determine approval status
                existing = existing_skills.get(skillhierarchy_id)
                approval_status = None
                approved_by = None
                
                if existing:
                    prev_level = existing["levelSelected"]
                    prev_status = existing["approvalStatus"]
                    prev_approved_by = existing.get("approvedByEmail")
                    
                    if prev_status == "Approved" and prev_level == "L3" and level != "L3":
                        approval_status = "Pre-Approved"
                    elif prev_status == "Approved" and prev_level == "L3" and level == "L3":
                        # Keep existing approval - skip updating this skill but keep it in the list
                        skillhierarchy_ids_to_save.append(skillhierarchy_id)
                        continue
                    else:
                        if level == "L3":
                            approval_status = "Pending"
                            approved_by = manager_email.lower() if manager_email else None
                            pending_skills.append(sk)
                        else:
                            approval_status = "Pre-Approved"
                else:
                    if level == "L3":
                        approval_status = "Pending"
                        approved_by = manager_email.lower() if manager_email else None
                        pending_skills.append(sk)
                    else:
                        approval_status = "Pre-Approved"
                
                # Add to list of skills to save
                skillhierarchy_ids_to_save.append(skillhierarchy_id)
                
                skill_rows.append({
                    "employee_id": emp_id,
                    "skillhierarchy_id": skillhierarchy_id,
                    "levelSelected": level,
                    "approvalStatus": approval_status,
                    "approvedByEmail": approved_by,
                })
            
            # Delete skills that are no longer in the list
            if skillhierarchy_ids_to_save:
                delete_query = sql.SQL("""
                    DELETE FROM {employee_skill}
                    WHERE "employee_id" = %s 
                    AND "skillhierarchy_id" NOT IN %s
                """).format(employee_skill=sql.Identifier(schema, "EmployeeSkill"))
                with conn.cursor() as cur:
                    cur.execute(delete_query, (emp_id, tuple(skillhierarchy_ids_to_save)))
            else:
                # Delete all skills if none provided
                delete_all_query = sql.SQL("""
                    DELETE FROM {employee_skill}
                    WHERE "employee_id" = %s
                """).format(employee_skill=sql.Identifier(schema, "EmployeeSkill"))
                with conn.cursor() as cur:
                    cur.execute(delete_all_query, (emp_id,))
            
            # Delete existing skills that are being updated
            if skill_rows:
                ids_to_update = [row["skillhierarchy_id"] for row in skill_rows]
                delete_existing_query = sql.SQL("""
                    DELETE FROM {employee_skill}
                    WHERE "employee_id" = %s 
                    AND "skillhierarchy_id" IN %s
                """).format(employee_skill=sql.Identifier(schema, "EmployeeSkill"))
                with conn.cursor() as cur:
                    cur.execute(delete_existing_query, (emp_id, tuple(ids_to_update)))
                
                # Insert new/updated skills
                insert_query = sql.SQL("""
                    INSERT INTO {employee_skill}
                        ("employee_id", "skillhierarchy_id", "levelSelected", 
                         "approvalStatus", "approvedByEmail", "requestedAt")
                    VALUES (%(employee_id)s, %(skillhierarchy_id)s, %(levelSelected)s,
                            %(approvalStatus)s, %(approvedByEmail)s, NOW())
                """).format(employee_skill=sql.Identifier(schema, "EmployeeSkill"))
                
                with conn.cursor() as cur:
                    cur.executemany(insert_query, skill_rows)
            
            conn.commit()
            
            return {
                "message": f"Skills saved for {email}",
                "pending_skills_sent_to": manager_email.lower() if pending_skills and manager_email else None,
                "pending_count": len(pending_skills),
                "saved_count": len(skill_rows),
            }
            
        except Exception as e:
            conn.rollback()
            raise e


def dev_v2_save_employee_skill(request: Request):
    """
    Cloud Function entry point.
    Accepts POST with email and skills array.
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }
    
    try:
        if request.method != "POST":
            return (json.dumps({"error": "Method not allowed"}), 405, headers)
        
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        skills = data.get("skills", [])
        manager_email = data.get("managerEmail", "")
        
        if not email:
            return (json.dumps({"error": "Missing required field: email"}), 400, headers)
        
        if skills is None:
            return (json.dumps({"error": "Missing required field: skills"}), 400, headers)
        
        email = str(email).strip().lower()
        
        result = save_employee_skills_v2(email, skills, manager_email)
        
        return (json.dumps(result), 200, headers)
        
    except ValueError as e:
        return (json.dumps({"error": str(e)}), 404, headers)
    except psycopg2.Error as exc:
        logger.exception("Database error in save_employee_skill")
        return (json.dumps({"error": f"Database error: {str(exc)}"}), 500, headers)
    except Exception as exc:
        logger.exception("Error in save_employee_skill")
        return (json.dumps({"error": str(exc)}), 500, headers)


"""
Deployment command (Development):

gcloud functions deploy dev_v2_save_employee_skill \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_save_employee_skill \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development

Local testing command:
    functions-framework --target=dev_v2_save_employee_skill --source main.py --debug --port=8080
"""

