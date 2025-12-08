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


def get_master_skills(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    try:
        engine, session = create_database()

        sql = text(
            """
             SELECT json_agg(
                json_build_object(
                    'hashId', "hashId",
                    'Category', category,
                    'Sub-Category', subcategory,
                    'Sub-Sub-Category', subsubcategory,
                    'Tools', tools,
                    'L1', "L1",
                    'L2', "L2",
                    'L3', "L3"
                )
            ) AS skills
            FROM "MasterSkills";
        """
        )

        start_time = 0
        with engine.connect() as connection:
            start_time = time.time()
            result = connection.execute(sql).scalar_one()

        # ✅ End timing
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"⏱ Time taken to fetch master skills: {duration:.4f} seconds")

        logger.info("✅ Loaded master skills directly with raw SQL")
        return cors_response(result)

    except SQLAlchemyError:
        logger.exception("❌ Database error while fetching skills")
        return cors_response({"error": "Database connection error"}, 500)

    except Exception as e:
        logger.exception("❌ Unexpected error in get_master_skills")
        return cors_response({"error": str(e)}, 500)


"""
Deployment command (Production):
gcloud functions deploy get_master_skills
  --runtime python310
  --trigger-http
  --entry-point get_master_skills
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_get_master_skills
  --runtime python310
  --trigger-http
  --entry-point get_master_skills
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=development
"""
