import logging
import requests
from sqlalchemy import text, bindparam
from flask import jsonify, make_response
from db.database import create_database, load_config

logger = logging.getLogger(__name__)

CONFIG = load_config()
SEND_EMAIL_URL = f"{CONFIG.get('BASE_URL', '')}send_mail"
EMAIL_TEMPLATE = CONFIG.get("EMAIL_TEMPLATE", "")


def cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def save_employee_skills(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != "POST":
        return cors_response({"error": "Method not allowed"}, 405)

    try:
        data = request.get_json(silent=True)
        if not data or not data.get("email") or data.get("skills") is None:
            logger.error("❌ Missing required fields in request")
            return cors_response(
                {"error": "Missing required fields: email or skills"}, 400
            )

        email = str(data["email"]).lower()
        skills = data["skills"]

        engine, _ = create_database()

        # ✅ Use ONE transactional connection for all DB work
        with engine.begin() as conn:
            emp_query = text(
                'SELECT id, "managerEmail", name FROM "Employee" WHERE email = :email'
            )
            emp_result = conn.execute(emp_query, {"email": email}).fetchone()

            if not emp_result:
                logger.warning(f"⚠️ Employee not found for {email}")
                return cors_response({"error": "Employee not found"}, 404)

            emp_id, manager_email_db, emp_name = emp_result
            manager_email = data.get("managerEmail", "").lower()

            # Update manager email if not already set
            if manager_email and not manager_email_db:
                conn.execute(
                    text(
                        'UPDATE "Employee" SET "managerEmail" = :manager WHERE id = :emp_id'
                    ),
                    {"manager": manager_email, "emp_id": emp_id},
                )

            master_skill_map = {
                row["hashId"]: row["tools"]
                for row in conn.execute(
                    text('SELECT "hashId", "tools" FROM "MasterSkills"')
                ).mappings()
            }
            # Fetch all existing skills for this employee
            existing_sql = text(
                'SELECT "skillHashId", "levelSelected", "approvalStatus" '
                'FROM "EmployeeSkills" WHERE "empId" = :emp_id'
            )
            existing_skills = {
                row["skillHashId"]: {
                    "Level": row["levelSelected"],
                    "Status": row["approvalStatus"],
                }
                for row in conn.execute(existing_sql, {"emp_id": emp_id}).mappings()
            }

            skill_rows = []
            pending_skills = []

            for sk in skills:
                hash_id = sk.get("hashId")
                level = sk.get("Level")

                if not hash_id or not level:
                    continue

                existing = existing_skills.get(hash_id)
                approval_status = None
                approved_by = None

                if existing:
                    prev_level = existing["Level"]
                    prev_status = existing["Status"]

                    if (
                        prev_status == "Approved"
                        and prev_level == "L3"
                        and level != "L3"
                    ):
                        approval_status = "Pre-Approved"
                    elif (
                        prev_status == "Approved"
                        and prev_level == "L3"
                        and level == "L3"
                    ):
                        continue
                    else:
                        if level == "L3":
                            approval_status = "Pending"
                            approved_by = manager_email
                            pending_skills.append(sk)
                        else:
                            approval_status = "Pre-Approved"
                else:
                    if level == "L3":
                        approval_status = "Pending"
                        approved_by = manager_email
                        pending_skills.append(sk)
                    else:
                        approval_status = "Pre-Approved"

                skill_rows.append(
                    {
                        "empId": emp_id,
                        "skillHashId": hash_id,
                        "levelSelected": level,
                        "approvalStatus": approval_status,
                        "approvedByEmail": approved_by,
                    }
                )

            # 🧹 Delete all existing skills first if skills array is empty or reduced
            if not skills:
                # Delete all skills if none provided
                conn.execute(
                    text('DELETE FROM "EmployeeSkills" WHERE "empId" = :emp_id'),
                    {"emp_id": emp_id},
                )
            else:
                current_hash_ids = [
                    sk.get("hashId") for sk in skills if sk.get("hashId")
                ]
                if current_hash_ids:
                    delete_missing_sql = text(
                        'DELETE FROM "EmployeeSkills" '
                        'WHERE "empId" = :emp_id AND "skillHashId" NOT IN :hash_ids'
                    ).bindparams(bindparam("hash_ids", expanding=True))
                    conn.execute(
                        delete_missing_sql,
                        {"emp_id": emp_id, "hash_ids": current_hash_ids},
                    )

            # 🧩 Step 2: Prepare upserts (insert or replace)
            if skill_rows:
                hash_ids = [row["skillHashId"] for row in skill_rows]
                delete_existing_sql = text(
                    'DELETE FROM "EmployeeSkills" '
                    'WHERE "empId" = :emp_id AND "skillHashId" IN :hash_ids'
                ).bindparams(bindparam("hash_ids", expanding=True))
                conn.execute(
                    delete_existing_sql, {"emp_id": emp_id, "hash_ids": hash_ids}
                )

                insert_sql = text(
                    """
                    INSERT INTO "EmployeeSkills"
                    ("empId", "skillHashId", "levelSelected", "approvalStatus", "approvedByEmail", "requestedAt")
                    VALUES (:empId, :skillHashId, :levelSelected, :approvalStatus, :approvedByEmail, NOW())
                    """
                )
                conn.execute(insert_sql, skill_rows)

        if pending_skills and manager_email:
            skills_list = [
                master_skill_map.get(sk.get("hashId"), sk.get("hashId"))
                for sk in pending_skills
            ]

            # Limit visible skills
            if len(skills_list) > 5:
                visible = skills_list[:5]
                hidden = len(skills_list) - 5
                formatted_skills = "".join(f"<li>{s}</li>" for s in visible)
                formatted_skills += f"<li><em>+{hidden} more</em></li>"
            else:
                formatted_skills = "".join(f"<li>{s}</li>" for s in skills_list)

            html_body = (
                EMAIL_TEMPLATE.replace("{{requestee_name}}", emp_name or email)
                .replace("{{requested_skills}}", formatted_skills)
                .replace("{{skill_matrix_url}}", CONFIG.get("APP_URL", "#"))
            )

            subject = f"Skill Review Request from {emp_name or email}"
            email_payload = {"to": manager_email, "subject": subject, "body": html_body}

            try:
                logger.info(f"📧 Sending review request email to {manager_email}")
                response = requests.post(SEND_EMAIL_URL, json=email_payload)
                if response.status_code != 200:
                    logger.warning(
                        f"⚠️ Email service returned {response.status_code}: {response.text}"
                    )
                else:
                    logger.info("✅ Email sent successfully.")
            except Exception as e:
                logger.exception(f"❌ Failed to call send_mail endpoint: {e}")

        return cors_response(
            {
                "message": f"Skills saved for {email}",
                "pending_skills_sent_to": manager_email if pending_skills else None,
                "pending_count": len(pending_skills),
            },
            200,
        )
    except Exception as e:
        logger.exception("Error in save_employee_skills")
        return cors_response({"error": str(e)}, 500)


"""
Deployment command (Production):
gcloud functions deploy save_employee_skills
    --runtime python310
    --trigger-http
    --entry-point save_employee_skills
    --service-account training-project-419308@appspot.gserviceaccount.com
    --allow-unauthenticated
    --no-gen2
    --region asia-south1
    --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_save_employee_skills
    --runtime python310
    --trigger-http
    --entry-point save_employee_skills
    --service-account training-project-419308@appspot.gserviceaccount.com
    --allow-unauthenticated
    --no-gen2
    --region asia-south1
    --set-env-vars ENV=development
"""
"""
Local testing command:
    functions-framework --target=save_employee_skills --port=8084 --debug 
"""
