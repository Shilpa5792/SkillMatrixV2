import os
import json
import logging
from datetime import datetime, timedelta
from flask import Request, jsonify, make_response
from google.cloud import storage
from db.database import create_database, load_config
from sqlalchemy import text

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

config = load_config()
BUCKET_NAME = config.get("BUCKET_NAME")
storage_client = storage.Client()


def cors_response(data, status=200):
    """Helper function to add CORS headers to any response"""
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def upload_cv(request):
    """Uploads an employee CV file (PDF/DOC/DOCX) to GCS and updates employee record with blob path, returning a signed URL."""
    if request.method == "OPTIONS":
        return cors_response({}, 204)

    if request.method != "POST":
        return cors_response({"error": "Method not allowed"}, 405)

    try:
        # Get employee email
        employee_email = request.form.get("employeeEmail")
        if not employee_email:
            return cors_response({"error": "Missing employeeEmail field"}, 400)
        employee_email = employee_email.lower()

        # Get uploaded file
        file = request.files.get("file")
        if not file:
            return cors_response({"error": "No file uploaded"}, 400)

        # Validate file type
        allowed_extensions = (".pdf", ".doc", ".docx")
        filename = file.filename.lower()
        if not filename.endswith(allowed_extensions):
            return cors_response(
                {"error": "Invalid file type. Only PDF, DOC, or DOCX allowed."}, 400
            )

        # Timestamp
        now = datetime.utcnow()
        timestamp = now.strftime("%d%m%Y_%H%M%S")
        file_ext = os.path.splitext(filename)[1]
        blob_name = f"employee-cv/{employee_email}/cv_{timestamp}{file_ext}"

        # Upload to GCS
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.upload_from_file(
            file, content_type=file.content_type or "application/octet-stream"
        )

        # Generate a signed URL valid for 2 days
        # signed_url = blob.generate_signed_url(expiration=timedelta(days=2))
        blob.make_public()

        # Store only the blob path in the database
        engine, _ = create_database()
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE "Employee"
                    SET "cvPublicUrl" = :cv_blob_path
                    WHERE "email" = :email
                    """
                ),
                {"cv_blob_path": blob.public_url, "email": employee_email},
            )
            if result.rowcount == 0:
                return cors_response(
                    {"error": f"Employee with email {employee_email} not found."},
                    404,
                )

        # Optionally store metadata in GCS (not public)
        blob.metadata = {
            "employeeEmail": employee_email,
            "uploadedAt": now.isoformat(),
        }
        blob.patch()

        return cors_response(
            {
                "message": "CV uploaded successfully",
                # "signedUrl": signed_url,
                "cvUrl": blob.public_url,
                "fileName": file.filename,
            },
            200,
        )

    except Exception as e:
        logger.exception("❌ Error uploading CV")
        return cors_response({"error": str(e)}, 500)


"""
Deployment command (Production):
gcloud functions deploy upload_cv
    --runtime python310
    --trigger-http
    --entry-point upload_cv
    --service-account training-project-419308@appspot.gserviceaccount.com
    --allow-unauthenticated
    --no-gen2
    --region asia-south1
    --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_upload_cv
    --runtime python310
    --trigger-http
    --entry-point upload_cv
    --service-account training-project-419308@appspot.gserviceaccount.com
    --allow-unauthenticated
    --no-gen2
    --region asia-south1
    --set-env-vars ENV=development
"""
"""
Local testing command:
functions-framework --target=upload_cv --port=8084 --debug 
"""
