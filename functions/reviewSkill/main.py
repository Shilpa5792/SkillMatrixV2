import logging
from flask import jsonify, make_response
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


def review_skill(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method == "POST":
        try:
            data = request.get_json(silent=True)
            if not data:
                return cors_response({"error": "Missing JSON body"}, 400)

            approved_by = str(data.get("approvedByEmail", "")).lower()
            action = data.get("action")
            reason = data.get("reason", None)
            raw_skills = data.get("skills", [])

            skill_ids = [
                sk["empSkillId"] if isinstance(sk, dict) else sk
                for sk in raw_skills
                if sk
            ]
            # ✅ Validate
            if not approved_by or not action or not raw_skills:
                return cors_response(
                    {
                        "error": "Missing required fields: approvedByEmail, action, or skills"
                    },
                    400,
                )

            if action not in ["approve", "reject"]:
                return cors_response(
                    {"error": "Invalid action. Must be 'approve' or 'reject'."}, 400
                )

            if action == "reject" and not reason:
                return cors_response(
                    {"error": "Rejection reason required for rejection"}, 400
                )

            engine, _ = create_database()

            # Convert to lower for consistency
            approved_by = approved_by.lower()
            # skill_ids = [sk.get("empSkillId") for sk in skills if sk.get("empSkillId")]

            if not skill_ids:
                return cors_response({"error": "No valid skill IDs provided"}, 400)

            with engine.begin() as conn:
                # Fetch all skill records first
                fetch_sql = text(
                    'SELECT id, "approvalStatus", "approvedByEmail" '
                    'FROM "EmployeeSkills" WHERE id = ANY(:ids)'
                )
                existing = conn.execute(fetch_sql, {"ids": skill_ids}).mappings().all()

                if not existing:
                    return cors_response({"error": "No matching skills found"}, 404)

                unauthorized = []
                updates = []

                for row in existing:
                    skill_id = row["id"]
                    current_approver = (row["approvedByEmail"] or "").lower()

                    # Ensure correct manager is approving
                    if current_approver and current_approver != approved_by:
                        unauthorized.append(skill_id)
                        continue

                    new_status = "Approved" if action == "approve" else "Rejected"
                    new_level = "L3" if action == "approve" else "L2"

                    updates.append(
                        {
                            "skillId": skill_id,
                            "status": new_status,
                            "reason": reason if action == "reject" else None,
                            "level": new_level,
                        }
                    )

                # Reject unauthorized
                if unauthorized:
                    return cors_response(
                        {
                            "error": "Unauthorized to review some skills",
                            "unauthorizedSkillIds": unauthorized,
                        },
                        403,
                    )

                if not updates:
                    return cors_response({"message": "No skills to update"}, 200)

                # Bulk update
                update_sql = text(
                    """
                    UPDATE "EmployeeSkills"
                    SET 
                        "approvalStatus" = :status,
                        "rejectionReason" = :reason,
                        "levelSelected" = :level,
                        "reviewedAt" = NOW()
                    WHERE id = :skillId
                    """
                )
                conn.execute(update_sql, updates)

            logger.info("Bulk skill review (%s) completed by %s", action, approved_by)
            return cors_response(
                {"message": f"{len(updates)} skills {action}d successfully"},
                200,
            )

        except Exception as e:
            logger.exception("❌ Error reviewing skills")
            return cors_response({"error": str(e)}, 500)

    return cors_response({"error": "Method not allowed"}, 405)


"""
Deployment command (Production):
gcloud functions deploy review_skill
  --runtime python310
  --trigger-http
  --entry-point review_skill
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_review_skill
  --runtime python310
  --trigger-http
  --entry-point review_skill
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=development
"""
"""
Local testing command:
functions-framework --target=review_skill --port=8084 --debug 
"""
