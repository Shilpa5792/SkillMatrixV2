import logging
from flask import jsonify, make_response
import time
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


import time
import json
import logging
from flask import make_response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from db.database import create_database

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def cors_response(data, status=200):
    """Utility to handle CORS-friendly JSON responses"""
    if not isinstance(data, str):
        data = json.dumps(data, indent=2)

    response = make_response(data, status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Content-Type"] = "application/json"
    return response


def get_master_certificates(request):
    # ✅ Handle CORS preflight
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    try:
        # ✅ Setup DB
        engine, session = create_database()

        # ✅ Correct SQL for MasterCertificate
        sql = text(
            """
            SELECT json_agg(
                json_build_object(
                    'hashId', "hashId",
                    'certProvider', "certProvider",
                    'certName', "certName",
                    'certLevel', "certLevel",
                    'validYears', "validYears"
                )
            ) AS certificates
            FROM "MasterCertificate"
            WHERE "isActive" = 1
            ;
            """
        )

        start_time = time.time()
        with engine.connect() as connection:
            result = connection.execute(sql).scalar_one_or_none()
        end_time = time.time()

        logger.info(f"✅ Loaded master certificates in {end_time - start_time:.4f}s")

        # If no data found
        if not result:
            result = []

        return cors_response(result)

    except Exception as e:
        logger.exception("❌ Unexpected error in get_master_certificates")
        return cors_response({"error": str(e)}, 500)


"""
Deployment command (Production):
gcloud functions deploy get_master_certificates
  --runtime python310
  --trigger-http
  --entry-point get_master_certificates
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""

