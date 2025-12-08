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


def save_employee(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != "POST":
        return cors_response({"error": "Method not allowed"}, 405)
    try:
        data = request.get_json()
        data["userPrincipalName"] = str(data["userPrincipalName"]).lower()
        print(request)
        # data["email"] = str(data["userPrincipalName"]).lower()
        if not data:
            return cors_response({"error": "Missing JSON body"}, 400)

        required = ["employeeId", "userPrincipalName", "displayName"]
        if not all(data.get(f) for f in required):
            return cors_response({"error": f"Missing required fields {required}"}, 400)

        engine, _ = create_database()

        with engine.begin() as conn:
            # 1. Check if employee exists
            check_sql = text(
                """SELECT "managerEmail", "cvPublicUrl" FROM "Employee" 
                                WHERE email = :email"""
            )
            result = conn.execute(
                check_sql, {"email": data["userPrincipalName"]}
            ).fetchone()

            if result:
                # Employee exists → update details
                update_sql = text(
                    """
                    UPDATE "Employee"
                    SET "empId"   = :id,
                        name = :name,
                        "jobTitle"     = :job,
                        department    = :dept
                    WHERE email = :email
                """
                )
                conn.execute(
                    update_sql,
                    {
                        "id": data["employeeId"],
                        "name": data["displayName"],
                        "job": data.get("jobTitle"),
                        "dept": data.get("department"),
                        "email": data["userPrincipalName"],
                    },
                )
                logger.info("Updated employee %s", data["userPrincipalName"])
                return cors_response(
                    {"managerEmail": result[0] or "", "cvPublicUrl": result[1] or ""},
                    200,
                )

            else:
                insert_sql = text(
                    """
                    INSERT INTO "Employee"
                        ("empId", email, name, "jobTitle", department)
                    VALUES (:id, :email, :name, :job, :dept)
                """
                )
                conn.execute(
                    insert_sql,
                    {
                        "id": data["employeeId"],
                        "email": data["userPrincipalName"],
                        "name": data["displayName"],
                        "job": data.get("jobTitle"),
                        "dept": data.get("department"),
                    },
                )
                logger.info("Created new employee %s", data["userPrincipalName"])
                return cors_response({"managerEmail": "", "cvPublicUrl": ""}, 200)

    except Exception as e:
        logger.exception("❌ Unexpected error in save_sso_user")
        return cors_response({"error": str(e)}, 500)


"""
Deployment command (Production):
gcloud functions deploy save_employee
  --runtime python310
  --trigger-http
  --entry-point save_employee
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_save_employee
  --runtime python310
  --trigger-http
  --entry-point save_employee
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=development
"""
"""
Local testing command:
functions-framework --target=save_employee --port=8084 --debug 
"""
