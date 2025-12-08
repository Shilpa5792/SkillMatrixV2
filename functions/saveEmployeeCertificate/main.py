import logging
import requests
from sqlalchemy import text
from flask import jsonify, make_response
from db.database import create_database, load_config
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


CONFIG = load_config()
SEND_EMAIL_URL = f"{CONFIG.get('BASE_URL', '')}send_mail"
EMAIL_TEMPLATE = CONFIG.get("EMAIL_TEMPLATE", "")


def cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def save_employee_certificate(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != "POST":
        return cors_response({"error": "Method not allowed"}, 405)

    try:
        payload = request.get_json(silent=True)
        if (
            not payload
            or not payload.get("email")
            or payload.get("certificates") is None
        ):
            logger.error("❌ Missing required fields in request")
            return cors_response(
                {"error": "Missing required fields: email or certificates"}, 400
            )

        email = str(payload["email"]).lower()
        manager_email = (payload.get("managerEmail") or "").lower()
        certs = payload.get("certificates", [])

        engine, _ = create_database()

        with engine.begin() as conn:
            # Validate employee existence
            emp_query = text(
                'SELECT id, "managerEmail", name FROM "Employee" WHERE email = :email'
            )
            emp_row = conn.execute(emp_query, {"email": email}).fetchone()
            if not emp_row:
                logger.warning(f"⚠️ Employee not found for {email}")
                return cors_response({"error": "Employee not found"}, 404)

            emp_id, manager_email_db, emp_name = emp_row

            if not manager_email_db and manager_email:
                conn.execute(
                    text('UPDATE "Employee" SET "managerEmail" = :m WHERE id = :id'),
                    {"m": manager_email, "id": emp_id},
                )

            # ✅ Prefer passed manager_email if available, else from DB, else empty
            final_manager_email = manager_email or (manager_email_db or "")

            # Fetch existing employee certificates (use emp_id now)
            existing_q = text(
                'SELECT "certHashId", "approvalStatus" '
                'FROM "EmployeeCertificate" WHERE "empId" = :emp_id'
            )
            existing_rows = {
                row["certHashId"]: row["approvalStatus"]
                for row in conn.execute(existing_q, {"emp_id": emp_id}).mappings()
            }

            incoming_hashes = set()
            to_upsert = []
            pending_for_email = []

            for c in certs:
                certProvider = (c.get("certProvider") or "").strip()
                certName = (c.get("certName") or "").strip()
                if not certProvider or not certName:
                    logger.info("Skipping certificate entry with missing provider/name")
                    continue

                certHashId = c.get("certHashId")
                incoming_hashes.add(certHashId)

                certLevel = c.get("certLevel")
                yearAchieved = c.get("yearAchieved", "")
                expiryDate = c.get("expiryDate", "")
                certLink = c.get("certLink", "")
                certIdExternal = c.get("certIdExternal", "")

                # Skip existing Approved ones
                existing_status = existing_rows.get(certHashId)
                if existing_status == "Approved":
                    logger.info(
                        f"✅ Certificate {certHashId} already approved for {email}, skipping update."
                    )
                    continue

                # Always store as Pending
                approvalStatus = "Pending"

                to_upsert.append(
                    {
                        "certHashId": certHashId,
                        "empId": emp_id,
                        "certProvider": certProvider,
                        "certName": certName,
                        "certLevel": certLevel,
                        "yearAchieved": yearAchieved,
                        "expiryDate": expiryDate,
                        "certLink": certLink,
                        "certIdExternal": certIdExternal,
                        "isVerified": 0,
                        "approvalStatus": approvalStatus,
                        "rejectionReason": None,
                        "requestedAt": datetime.utcnow(),
                        "approvedByEmail": final_manager_email,  # ✅ Added here
                    }
                )

                pending_for_email.append(
                    {
                        "certHashId": certHashId,
                        "display": f"{certProvider} - {certName}",
                    }
                )

            # Delete missing, non-approved certs
            existing_all_q = text(
                'SELECT "certHashId", "approvalStatus" FROM "EmployeeCertificate" WHERE "empId" = :emp_id'
            )
            existing_all = {
                r["certHashId"]: r["approvalStatus"]
                for r in conn.execute(existing_all_q, {"emp_id": emp_id}).mappings()
            }

            to_delete_hashes = [
                h
                for h, status in existing_all.items()
                if (h not in incoming_hashes and status != "Approved")
            ]

            if to_delete_hashes:
                delete_q = text(
                    'DELETE FROM "EmployeeCertificate" WHERE "empId" = :emp_id AND "certHashId" = :hash_id'
                )
                for h in to_delete_hashes:
                    conn.execute(delete_q, {"emp_id": emp_id, "hash_id": h})

            # Delete existing copies before reinsert (simplify update logic)
            for row in to_upsert:
                conn.execute(
                    text(
                        'DELETE FROM "EmployeeCertificate" WHERE "empId" = :emp_id AND "certHashId" = :hash_id'
                    ),
                    {"emp_id": emp_id, "hash_id": row["certHashId"]},
                )

            # Insert new/updated rows
            if to_upsert:
                insert_sql = text(
                    """
                    INSERT INTO "EmployeeCertificate"
                    ("certHashId","empId","certProvider","certName","certLevel",
                    "yearAchieved","expiryDate","certLink","certIdExternal",
                    "isVerified","approvalStatus","rejectionReason","requestedAt","approvedByEmail")
                    VALUES (:certHashId,:empId,:certProvider,:certName,:certLevel,
                    :yearAchieved,:expiryDate,:certLink,:certIdExternal,
                    :isVerified,:approvalStatus,:rejectionReason,:requestedAt,:approvedByEmail)
                    """
                )
                conn.execute(insert_sql, to_upsert)

        return cors_response(
            {
                "message": f"Certificates processed for {email}",
                "deleted_count": len(to_delete_hashes),
                "upserted_count": len(to_upsert),
            },
            200,
        )

    except Exception as e:
        logger.exception("Error in save_employee_certificate")
        return cors_response({"error": str(e)}, 500)


"""
Deployment command (Production):
gcloud functions deploy save_employee_certificate
    --runtime python310
    --trigger-http
    --entry-point save_employee_certificate
    --service-account training-project-419308@appspot.gserviceaccount.com
    --allow-unauthenticated
    --no-gen2
    --region asia-south1
    --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_save_employee_certificate
    --runtime python310
    --trigger-http
    --entry-point save_employee_certificate
    --service-account training-project-419308@appspot.gserviceaccount.com
    --allow-unauthenticated
    --no-gen2
    --region asia-south1
    --set-env-vars ENV=development
"""
"""
Local testing command:
    functions-framework --target=save_employee_certificate --port=8084 --debug 
"""
