import logging
from flask import jsonify, make_response, request
from sqlalchemy.exc import SQLAlchemyError
from db.database import create_database  # 👈 import here
from sqlalchemy import text

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def cors_response(data, status=200):
    """Helper function to add CORS headers to any response"""
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def update_manager_email(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method == "POST":
        try:
            data = request.get_json()
            if not data or not data.get("email") or not data.get("managerEmail"):
                return cors_response(
                    {"error": "Missing required fields: email or managerEmail"}, 400
                )

            email = str(data["email"]).lower()
            new_manager = str(data["managerEmail"]).lower()
            
            engine, _ = create_database()

            with engine.begin() as conn:
                # Single query to update and return the updated manager email
                update_sql = text(
                    'UPDATE "Employee" '
                    'SET "managerEmail" = :manager '
                    "WHERE email = :email "
                    'RETURNING "managerEmail"'
                )
                result = conn.execute(
                    update_sql, {"manager": new_manager, "email": email}
                ).fetchone()

                if not result:
                    return cors_response({"error": "Employee not found"}, 404)

            logger.info("Updated manager email for %s to %s", email, new_manager)
            return cors_response({"managerEmail": result[0]}, 200)

        except Exception as e:
            logger.exception("❌ Unexpected error in update_manager_email")
            return cors_response({"error": str(e)}, 500)

    return cors_response({"error": "Method not allowed"}, 405)


"""
Deployment command (Production):
gcloud functions deploy update_manager_email
  --runtime python310
  --trigger-http
  --entry-point update_manager_email
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_update_manager_email
  --runtime python310
  --trigger-http
  --entry-point update_manager_email
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=development
"""
"""
Local testing command:
functions-framework --target=update_manager_email --port=8084 --debug 
"""
