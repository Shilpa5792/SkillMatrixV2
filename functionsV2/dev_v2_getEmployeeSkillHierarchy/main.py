"""
Google Cloud Function that fetches employee skill hierarchy.
For managers: returns all subordinates' skills
For regular employees: returns only their own skills
"""

import json
from typing import Any, Dict, List, Optional

import psycopg2
from flask import Request
from psycopg2.extras import RealDictCursor

import db_utils


def get_employee_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch employee details by email."""
    query = """
        SELECT 
            id,
            name,
            email,
            jobtitle,
            department,
            manageremail
        FROM "Employee"
        WHERE email = %s
    """
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (email,))
        return cur.fetchone()


def get_subordinate_ids(manager_email: str) -> List[int]:
    """Recursively fetch all subordinate employee IDs for a manager."""
    query = """
        WITH RECURSIVE subordinates AS (
            -- Base case: direct reports
            SELECT id, email, manageremail
            FROM "Employee"
            WHERE manageremail = %s
            
            UNION ALL
            
            -- Recursive case: reports of reports
            SELECT e.id, e.email, e.manageremail
            FROM "Employee" e
            INNER JOIN subordinates s ON e.manageremail = s.email
        )
        SELECT id FROM subordinates
    """
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (manager_email,))
        results = cur.fetchall()
        return [row['id'] for row in results]


def is_manager(email: str) -> bool:
    """Check if an employee is a manager (has subordinates)."""
    query = """
        SELECT EXISTS(
            SELECT 1 FROM "Employee"
            WHERE manageremail = %s
        ) as is_manager
    """
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (email,))
        result = cur.fetchone()
        return result['is_manager'] if result else False


def fetch_employee_skills_hierarchy(employee_ids: List[int]) -> Dict[str, Any]:
    """Fetch skill hierarchy for given employee IDs."""
    query = """
        WITH employee_skills AS (
            SELECT DISTINCT
                es.employee_id,
                e.name as employee_name,
                e.email as employee_email,
                e.jobtitle as employee_jobtitle,
                e.department as employee_department,
                shl.domain_id,
                shl.discipline_id,
                shl.skill_id,
                shl.framework_id
            FROM "EmployeeSkill" es
            INNER JOIN "Employee" e ON es.employee_id = e.id
            INNER JOIN "SkillHierarchyLink" shl ON es.skillhierarchy_id = shl.id
            WHERE es.employee_id = ANY(%s)
        ),
        framework_agg AS (
            SELECT 
                es.employee_id,
                es.employee_name,
                es.employee_email,
                es.employee_jobtitle,
                es.employee_department,
                es.domain_id,
                es.discipline_id,
                es.skill_id,
                json_agg(
                    json_build_object(
                        'id', es.framework_id,
                        'name', mf.framework_name,
                        'label', 'Framework'
                    ) ORDER BY mf.framework_name
                ) FILTER (WHERE es.framework_id IS NOT NULL) as frameworks
            FROM employee_skills es
            LEFT JOIN "MasterFramework" mf ON es.framework_id = mf.id
            GROUP BY es.employee_id, es.employee_name, es.employee_email, 
                     es.employee_jobtitle, es.employee_department,
                     es.domain_id, es.discipline_id, es.skill_id
        ),
        skill_agg AS (
            SELECT 
                fa.employee_id,
                fa.employee_name,
                fa.employee_email,
                fa.employee_jobtitle,
                fa.employee_department,
                fa.domain_id,
                fa.discipline_id,
                json_agg(
                    json_build_object(
                        'id', fa.skill_id,
                        'name', ms.skill_name,
                        'label', 'Skill',
                        'children', COALESCE(fa.frameworks, '[]'::json)
                    ) ORDER BY ms.skill_name
                ) FILTER (WHERE fa.skill_id IS NOT NULL) as skills
            FROM framework_agg fa
            LEFT JOIN "MasterSkill" ms ON fa.skill_id = ms.id
            GROUP BY fa.employee_id, fa.employee_name, fa.employee_email,
                     fa.employee_jobtitle, fa.employee_department,
                     fa.domain_id, fa.discipline_id
        ),
        discipline_agg AS (
            SELECT 
                sa.employee_id,
                sa.employee_name,
                sa.employee_email,
                sa.employee_jobtitle,
                sa.employee_department,
                sa.domain_id,
                json_agg(
                    json_build_object(
                        'id', sa.discipline_id,
                        'name', mdisc.discipline_name,
                        'label', 'Discipline',
                        'children', COALESCE(sa.skills, '[]'::json)
                    ) ORDER BY mdisc.discipline_name
                ) FILTER (WHERE sa.discipline_id IS NOT NULL) as disciplines
            FROM skill_agg sa
            LEFT JOIN "MasterDiscipline" mdisc ON sa.discipline_id = mdisc.id
            GROUP BY sa.employee_id, sa.employee_name, sa.employee_email,
                     sa.employee_jobtitle, sa.employee_department, sa.domain_id
        ),
        domain_agg AS (
            SELECT 
                da.employee_id,
                da.employee_name,
                da.employee_email,
                da.employee_jobtitle,
                da.employee_department,
                json_agg(
                    json_build_object(
                        'id', da.domain_id,
                        'name', md.domain_name,
                        'label', 'Domain',
                        'children', COALESCE(da.disciplines, '[]'::json)
                    ) ORDER BY md.domain_name
                ) FILTER (WHERE da.domain_id IS NOT NULL) as domains
            FROM discipline_agg da
            LEFT JOIN "MasterDomain" md ON da.domain_id = md.id
            GROUP BY da.employee_id, da.employee_name, da.employee_email,
                     da.employee_jobtitle, da.employee_department
        )
        SELECT 
            json_agg(
                json_build_object(
                    'employee_id', employee_id,
                    'employee_name', employee_name,
                    'employee_email', employee_email,
                    'employee_jobtitle', employee_jobtitle,
                    'employee_department', employee_department,
                    'skill_hierarchy', COALESCE(domains, '[]'::json)
                ) ORDER BY employee_name
            ) as result
        FROM domain_agg
    """
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (employee_ids,))
        result = cur.fetchone()
        return result['result'] if result and result['result'] else []


def format_employee_with_children(employee_data: Dict[str, Any], skill_hierarchy: list) -> Dict[str, Any]:
    """
    Format employee data with the new children structure.
    
    Returns:
        {
            "employee_id": ...,
            "employee_name": ...,
            ...
            "children": [
                {
                    "name": "skills",
                    "children": [...]
                }
            ]
        }
    """
    return {
        'employee_id': employee_data['id'],
        'employee_name': employee_data['name'],
        'employee_email': employee_data['email'],
        'employee_jobtitle': employee_data['jobtitle'],
        'employee_department': employee_data['department'],
        'children': [
            {
                'name': 'skills',
                'children': skill_hierarchy
            }
        ]
    }


def dev_v2_get_employee_skills_hierarchy(request: Request):
    """
    Cloud Function entry point for getting employee skill hierarchy.
    
    Expected query parameter:
    - email: Employee email address (required)
    
    Returns:
    - For managers: Employee with children array containing skills and subordinates
    - For regular employees: Employee with children array containing only skills
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
        # Get email from query parameters
        email = request.args.get('email')
        
        if not email:
            error_response = {
                "status": "error",
                "message": "Email parameter is required"
            }
            return (json.dumps(error_response), 400, headers)
        
        # Get employee details
        employee = get_employee_by_email(email)
        
        if not employee:
            error_response = {
                "status": "error",
                "message": f"Employee with email '{email}' not found"
            }
            return (json.dumps(error_response), 404, headers)
        
        # Check if employee is a manager
        manager_status = is_manager(email)
        
        # Fetch the employee's own skills
        employee_skills_data = fetch_employee_skills_hierarchy([employee['id']])
        employee_skill_hierarchy = employee_skills_data[0]['skill_hierarchy'] if employee_skills_data else []
        
        # Format base employee structure with skills
        result = format_employee_with_children(employee, employee_skill_hierarchy)
        
        # If manager, add subordinates section
        if manager_status:
            subordinate_ids = get_subordinate_ids(email)
            
            if subordinate_ids:
                # Fetch all subordinates' data
                subordinates_data = fetch_employee_skills_hierarchy(subordinate_ids)
                
                # Format each subordinate with the new children structure
                formatted_subordinates = []
                for sub_data in subordinates_data:
                    subordinate_employee = get_employee_by_email(sub_data['employee_email'])
                    if subordinate_employee:
                        formatted_sub = format_employee_with_children(
                            subordinate_employee, 
                            sub_data['skill_hierarchy']
                        )
                        formatted_subordinates.append(formatted_sub)
                
                # Add subordinates section to children array
                result['children'].append({
                    'name': 'subordinates',
                    'children': formatted_subordinates
                })
            else:
                # Manager with no subordinates - still add empty subordinates section
                result['children'].append({
                    'name': 'subordinates',
                    'children': []
                })
        
        return (json.dumps(result), 200, headers)
        
    except psycopg2.Error as exc:
        error_response = {
            "status": "error",
            "message": f"Database error: {str(exc)}"
        }
        return (json.dumps(error_response), 500, headers)
    except Exception as exc:
        error_response = {
            "status": "error",
            "message": f"Internal error: {str(exc)}"
        }
        return (json.dumps(error_response), 500, headers)


"""
Deployment command (Development):

gcloud functions deploy dev_v2_get_employee_skills_hierarchy \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_employee_skills_hierarchy \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""

"""
Local testing command:

functions-framework --target=dev_v2_get_employee_skills_hierarchy --source main.py --debug --port=8080

Test URLs:
- Regular employee: http://127.0.0.1:8080/?email=employee@example.com
- Manager: http://127.0.0.1:8080/?email=manager@example.com
"""