import logging
from flask import jsonify, make_response, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from db.database import create_database

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def cors_response(data, status=200):
    """Helper function to add CORS headers to any response"""
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def get_expert_skill_request(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method == "GET":
        try:
            email = request.args.get("email")
            if not email:
                return cors_response(
                    {"error": "Missing required query param: email"}, 400
                )

            email = str(email).lower()
            engine, _ = create_database()
            with engine.begin() as conn:
                sql = text(
                    """
                    SELECT json_agg(
                        json_build_object(
                            'id', t.id,
                            'employee', t.name,
                            'skills', t.skills
                        )
                    ) AS result
                    FROM (
                        SELECT e.id,
                            e.name,
                            json_agg(
                                json_build_object(
                                    'Category', ms.category,
                                    'Sub-Category', ms.subcategory,
                                    'Sub-Sub-Category', ms.subsubcategory,
                                    'Tools', ms.tools,
                                    'Level', es."levelSelected",
                                    'hashId', es."skillHashId",
                                    'status', es."approvalStatus",
                                    'skillId', es.id
                                )
                            ) AS skills
                        FROM "EmployeeSkills" es
                        JOIN "Employee" e ON e."id" = es."empId"
                        JOIN "MasterSkills" ms ON ms."hashId" = es."skillHashId"
                        WHERE es."approvalStatus" = 'Pending'
                        AND es."levelSelected" = 'L3'
                        AND es."approvedByEmail" = :manager
                        GROUP BY e.id, e.name
                        ORDER BY e.id
                    ) t;
                    """
                )
                result = conn.execute(sql, {"manager": email}).scalar()

            if not result:
                return cors_response([], 200)

            return cors_response(result, 200)

        except Exception as e:
            logger.exception("❌ Error fetching expert skill requests")
            return cors_response({"error": str(e)}, 500)

    return cors_response({"error": "Method not allowed"}, 405)


"""
Deployment command (Production):
gcloud functions deploy get_expert_skill_request
  --runtime python310
  --trigger-http
  --entry-point get_expert_skill_request
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_get_expert_skill_request
  --runtime python310
  --trigger-http
  --entry-point get_expert_skill_request
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=development
"""
"""
Local testing command:
functions-framework --target=get_expert_skill_request --debug --port=8084
"""
