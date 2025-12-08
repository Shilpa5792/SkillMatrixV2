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


def get_employee_certificates(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # Handle POST
    if request.method == "POST":
        try:
            data = request.get_json(silent=True)
            if not data or not data.get("email"):
                return cors_response({"error": "Missing required field: email"}, 400)

            email = str(data["email"]).lower()

            # Create DB engine
            engine, _ = create_database()

            sql_emp = text("""SELECT id FROM "Employee" WHERE email = :email""")
            sql_cert = text(
                """
                SELECT json_agg(
                    json_build_object(
                        'certHashId', ec."certHashId",
                        'certProvider', ec."certProvider",
                        'certName', ec."certName",
                        'certLevel', ec."certLevel",
                        'validYears', mc."validYears",
                        'approvalStatus', ec."approvalStatus"
                    )
                ) AS certificates
                FROM "EmployeeCertificate" ec
                JOIN "MasterCertificate" mc
                  ON ec."certHashId" = mc."hashId"
                WHERE ec."empId" = :emp_id
                AND mc."isActive" = 1
                """
            )

            # Use a single DB connection
            with engine.connect() as connection:
                emp_result = connection.execute(sql_emp, {"email": email}).fetchone()

                if not emp_result:
                    logger.warning("⚠️ Employee with email %s not found", email)
                    return cors_response({"error": "Employee not found"}, 404)

                emp_id = emp_result[0]

                result = connection.execute(
                    sql_cert, {"emp_id": emp_id}
                ).scalar_one_or_none()

            # Always return a list
            certificates = result if result is not None else []

            logger.info("✅ Loaded certificates for employee %s", email)
            return cors_response(
                {"employeeEmail": email, "certificates": certificates}, 200
            )

        except Exception as e:
            logger.exception("❌ Unexpected error in get_employee_certificates")
            return cors_response({"error": str(e)}, 500)

    else:
        return cors_response({"error": "Method not allowed"}, 405)


"""
Production Deployment Command:

gcloud functions deploy get_employee_certificates
    --runtime python310
    --trigger-http
    --entry-point get_employee_certificates
    --service-account training-project-419308@appspot.gserviceaccount.com
    --allow-unauthenticated
    --no-gen2
    --region asia-south1
    --set-env-vars ENV=production
"""
"""
Development Deployment Command:

gcloud functions deploy dev_get_employee_certificates
    --runtime python310
    --trigger-http
    --entry-point get_employee_certificates
    --service-account training-project-419308@appspot.gserviceaccount.com
    --allow-unauthenticated
    --no-gen2
    --region asia-south1
    --set-env-vars ENV=development
"""
"""
Local testing command:
functions-framework --target=get_employee_certificates --debug --port=8084
"""
