"""
Google Cloud Function that saves/updates employee details in the Employee table.
Called when an employee logs in to ensure their details are up-to-date in the database.
"""

import json
import os
import logging
from typing import Dict, Optional, Any

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from flask import Request

import db_utils

logger = logging.getLogger(__name__)


def save_employee_details(
    employee_id: str,
    email: str,
    name: str,
    job_title: Optional[str] = None,
    department: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Save or update employee details in the Employee table.
    
    Args:
        employee_id: Employee ID (maps to empid column)
        email: Employee email (unique identifier)
        name: Employee display name
        job_title: Optional job title (maps to jobtitle column)
        department: Optional department
        
    Returns:
        Dictionary with managerEmail and cvPublicUrl if employee exists, empty strings otherwise
    """
    schema = os.getenv("DB_SCHEMA") or "public"
    
    with db_utils.get_db_connection() as conn:
        conn.autocommit = False
        
        try:
            # Normalize email to lowercase
            email_lower = email.lower().strip()
            
            # Check if employee exists - use SELECT * to get all columns
            # This handles cases where managerEmail or cvPublicUrl might not exist
            check_query = sql.SQL("""
                SELECT *
                FROM {employee}
                WHERE LOWER(email) = LOWER(%s)
            """).format(employee=sql.Identifier(schema, "Employee"))
            
            existing_employee = None
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(check_query, (email_lower,))
                result = cur.fetchone()
                if result:
                    existing_employee = dict(result)
            
            if existing_employee:
                # Employee exists → update details
                # Update empid, name, jobtitle, and department (all lowercase column names)
                update_query = sql.SQL("""
                    UPDATE {employee}
                    SET empid = %s,
                        name = %s,
                        jobtitle = %s,
                        department = %s,
                        updated_at = NOW()
                    WHERE LOWER(email) = LOWER(%s)
                """).format(employee=sql.Identifier(schema, "Employee"))
                
                with conn.cursor() as cur:
                    cur.execute(
                        update_query,
                        (
                            employee_id,
                            name,
                            job_title,
                            department,
                            email_lower,
                        ),
                    )
                
                conn.commit()
                logger.info(f"Updated employee {email_lower}")
                
                # Extract manageremail and cvpublicurl (all lowercase column names)
                manager_email = existing_employee.get("manageremail") or ""
                cv_url = existing_employee.get("cvpublicurl") or ""
                
                return {
                    "managerEmail": manager_email,
                    "cvPublicUrl": cv_url,
                    "message": "Employee details updated successfully",
                }
            else:
                # Employee doesn't exist → insert new employee
                # Insert empid, email, name, jobtitle, and department (all lowercase column names)
                insert_query = sql.SQL("""
                    INSERT INTO {employee}
                        (empid, email, name, jobtitle, department, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """).format(employee=sql.Identifier(schema, "Employee"))
                
                with conn.cursor() as cur:
                    cur.execute(
                        insert_query,
                        (
                            employee_id,
                            email_lower,
                            name,
                            job_title,
                            department,
                        ),
                    )
                
                conn.commit()
                logger.info(f"Created new employee {email_lower}")
                
                return {
                    "managerEmail": "",
                    "cvPublicUrl": "",
                    "message": "Employee created successfully",
                }
                
        except psycopg2.IntegrityError as e:
            conn.rollback()
            # Handle unique constraint violations
            if "email" in str(e):
                logger.error(f"Email {email_lower} already exists")
                raise ValueError(f"Email {email_lower} already exists")
            else:
                raise
        except Exception as e:
            conn.rollback()
            logger.exception(f"Error saving employee {email_lower}")
            raise


def dev_v2_save_employee(request: Request):
    """
    Cloud Function entry point for saving/updating employee details.
    Accepts POST with employeeId, userPrincipalName (email), displayName, jobTitle, department.
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
        
        # Extract required fields
        employee_id = data.get("employeeId")
        email = data.get("userPrincipalName")  # This is the email field from Azure AD
        name = data.get("displayName")
        
        # Validate required fields
        if not employee_id:
            return (
                json.dumps({"error": "Missing required field: employeeId"}),
                400,
                headers,
            )
        if not email:
            return (
                json.dumps({"error": "Missing required field: userPrincipalName"}),
                400,
                headers,
            )
        if not name:
            return (
                json.dumps({"error": "Missing required field: displayName"}),
                400,
                headers,
            )
        
        # Normalize email to lowercase
        email = str(email).lower().strip()
        
        # Extract optional fields
        job_title = data.get("jobTitle")
        department = data.get("department")
        
        # Save employee details
        result = save_employee_details(
            employee_id=str(employee_id),
            email=email,
            name=str(name),
            job_title=job_title,
            department=department,
        )
        
        return (json.dumps(result), 200, headers)
        
    except ValueError as e:
        return (json.dumps({"error": str(e)}), 400, headers)
    except psycopg2.Error as exc:
        logger.exception("Database error in save_employee")
        return (
            json.dumps({"error": f"Database error: {str(exc)}"}),
            500,
            headers,
        )
    except Exception as exc:
        logger.exception("Error in save_employee")
        return (json.dumps({"error": str(exc)}), 500, headers)


"""
Deployment command (Production):

gcloud functions deploy save_employee \
  --runtime python310 \
  --trigger-http \
  --entry-point save_employee \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""

"""
Deployment command (Development):

gcloud functions deploy dev_v2_save_employee \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_save_employee \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""

"""
Local testing command:

functions-framework --target=dev_v2_save_employee --source main.py --debug --port=8080

Test URL: http://127.0.0.1:8080/
Test with POST:
curl -X POST http://127.0.0.1:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "employeeId": "EMP001",
    "userPrincipalName": "test@example.com",
    "displayName": "Test User",
    "jobTitle": "Software Engineer",
    "department": "Engineering"
  }'
"""

