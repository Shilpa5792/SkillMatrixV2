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
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


def get_employee_skills(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method == "POST":
        try:
            data = request.get_json(silent=True)
            data["email"] = str(data["email"]).lower()
            if not data or not data.get("email"):
                return cors_response({"error": "Missing required field: email"}, 400)

            email = data["email"]
            engine, _ = create_database()

            # 1. Check if employee exists
            sql = text("""SELECT id FROM "Employee" WHERE email = :email""")
            with engine.connect() as connection:
                emp_result = connection.execute(sql, {"email": email}).fetchone()

            if not emp_result:
                logger.warning("⚠️ Employee with email %s not found", email)
                return cors_response({"error": "Employee not found"}, 404)

            emp_id = emp_result[0]

            # 2. Fetch skills
            sql = text(
                """
                SELECT json_agg(
                    json_build_object(
                        'hashId', s."hashId",
                        'Category', s.category,
                        'Sub-Category', s.subcategory,
                        'Sub-Sub-Category', s.subsubcategory,
                        'Tools', s.tools,
                        'Level', es."levelSelected",
                        'Status', es."approvalStatus",
                        'RejectReason',es."rejectionReason"
                    )
                ) AS skills
                FROM "EmployeeSkills" es
                JOIN "MasterSkills" s
                  ON es."skillHashId" = s."hashId"
                WHERE es."empId" = :emp_id
                """
            )

            with engine.connect() as connection:
                result = connection.execute(
                    sql, {"emp_id": emp_id}
                ).scalar_one_or_none()

            # ✅ Always return a list (not null)
            skills = result if result is not None else []

            logger.info("✅ Loaded skills for employee %s", email)
            return cors_response({"employeeEmail": email, "skills": skills}, 200)

        except Exception as e:
            logger.exception("❌ Unexpected error in get_employee_skills")
            return cors_response({"error": str(e)}, 500)
    else:
        return cors_response({"error": "Method not allowed"}, 405)


"""
Deployment command (Production):

gcloud functions deploy get_employee_skills
  --runtime python310
  --trigger-http
  --entry-point get_employee_skills
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""
"""
Deployment command (Development):

gcloud functions deploy dev_get_employee_skills
  --runtime python310
  --trigger-http
  --entry-point get_employee_skills
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=development
"""
"""
Local testing command:
functions-framework --target=get_employee_skills --debug --port=8084
"""
