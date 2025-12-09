"""
Google Cloud Function that fetches complete skill hierarchy.
"""

import json
from typing import Any, Dict

import psycopg2
from flask import Request
from psycopg2.extras import RealDictCursor

import db_utils


def fetch_complete_hierarchy() -> Dict[str, Any]:
    """Fetch complete skill hierarchy from the database."""
    query = """
        WITH framework_agg AS (
            SELECT 
                shl.domain_id,
                shl.discipline_id,
                shl.skill_id,
                json_agg(
                    json_build_object(
                        'id', shl.framework_id,
                        'name', mf.framework_name,
                        'label', 'Framework'
                    ) ORDER BY mf.framework_name
                ) as frameworks
            FROM "SkillHierarchyLink" shl
            LEFT JOIN "MasterFramework" mf ON shl.framework_id = mf.id
            GROUP BY shl.domain_id, shl.discipline_id, shl.skill_id
        ),
        skill_agg AS (
            SELECT 
                fa.domain_id,
                fa.discipline_id,
                json_agg(
                    json_build_object(
                        'id', fa.skill_id,
                        'name', ms.skill_name,
                        'label', 'Skill',
                        'children', fa.frameworks
                    ) ORDER BY ms.skill_name
                ) as skills
            FROM framework_agg fa
            LEFT JOIN "MasterSkill" ms ON fa.skill_id = ms.id
            GROUP BY fa.domain_id, fa.discipline_id
        ),
        discipline_agg AS (
            SELECT 
                sa.domain_id,
                json_agg(
                    json_build_object(
                        'id', sa.discipline_id,
                        'name', mdisc.discipline_name,
                        'label', 'Discipline',
                        'children', sa.skills
                    ) ORDER BY mdisc.discipline_name
                ) as disciplines
            FROM skill_agg sa
            LEFT JOIN "MasterDiscipline" mdisc ON sa.discipline_id = mdisc.id
            GROUP BY sa.domain_id
        )
        SELECT 
            json_agg(
                json_build_object(
                    'id', da.domain_id,
                    'name', md.domain_name,
                    'label', 'Domain',
                    'children', da.disciplines
                ) ORDER BY md.domain_name
            ) as hierarchy
        FROM discipline_agg da
        LEFT JOIN "MasterDomain" md ON da.domain_id = md.id
    """
    
    with db_utils.get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        result = cur.fetchone()
        return result['hierarchy'] if result and result['hierarchy'] else []


def calculate_hierarchy_counts(data: list) -> Dict[str, int]:
    """Calculate counts for domains, disciplines, skills, and frameworks."""
    total_domains = len(data)
    total_disciplines = sum(len(domain.get('children', [])) for domain in data)
    total_skills = sum(
        len(discipline.get('children', [])) 
        for domain in data 
        for discipline in domain.get('children', [])
    )
    total_frameworks = sum(
        len(skill.get('children', [])) 
        for domain in data 
        for discipline in domain.get('children', [])
        for skill in discipline.get('children', [])
    )
    
    return {
        'total_domains': total_domains,
        'total_disciplines': total_disciplines,
        'total_skills': total_skills,
        'total_frameworks': total_frameworks
    }


def dev_v2_get_complete_hierarchy(request: Request):
    """
    Cloud Function entry point for getting complete skill hierarchy.
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
        data = fetch_complete_hierarchy()
        
        # Calculate counts
        counts = calculate_hierarchy_counts(data)
        
        response_data = {
            "status": "success",
            **counts,
            "data": data
        }
        
        return (json.dumps(response_data), 200, headers)
        
    except psycopg2.Error as exc:
        error_response = {"status": "error", "message": str(exc)}
        return (json.dumps(error_response), 500, headers)
    except Exception as exc:
        error_response = {"status": "error", "message": str(exc)}
        return (json.dumps(error_response), 500, headers)


"""
Deployment command (Production):

gcloud functions deploy get_complete_hierarchy \
  --runtime python310 \
  --trigger-http \
  --entry-point get_complete_hierarchy \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=production
"""

"""
Deployment command (Development):

gcloud functions deploy dev_v2_get_complete_hierarchy \
  --runtime python310 \
  --trigger-http \
  --entry-point dev_v2_get_complete_hierarchy \
  --service-account training-project-419308@appspot.gserviceaccount.com \
  --allow-unauthenticated \
  --no-gen2 \
  --region asia-south1 \
  --set-env-vars ENV=development
"""

"""
Local testing command:

functions-framework --target=dev_v2_get_complete_hierarchy --source main.py --debug --port=8080

Test URL: http://127.0.0.1:8080/
"""