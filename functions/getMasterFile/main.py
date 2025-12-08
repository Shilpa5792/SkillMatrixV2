import datetime
from flask import jsonify, Request, make_response
from google.cloud import storage
import json

with open("config.json") as f:
    config = json.load(f)

BUCKET_NAME = config["BUCKET_NAME"]
storage_client = storage.Client()


def cors_response(data, status=200):
    """Helper function to add CORS headers to any response"""
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# download the csv and send it to frontend
def get_master_file(request: Request):
    """Download master Skills or Certificates file as CSV/XLSX"""
    if request.method == "OPTIONS":
        # CORS preflight
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # Determine which master file to download
    master_type = request.args.get(
        "type", ""
    ).lower()  # expects "skills" or "certificates"
    if master_type not in ["skills", "certificates"]:
        return cors_response(
            {"error": "Invalid type. Use 'skills' or 'certificates'."}, 400
        )

    try:
        # Determine filename in bucket
        prefix = (
            "INFOLDER/Master_Skills"
            if master_type == "skills"
            else "INFOLDER/Master_Certificates"
        )

        # Search for the file (CSV or XLSX)
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix=prefix))

        if not blobs:
            return cors_response(
                {"error": f"No master file found for '{master_type}'."}, 404
            )

        # Take the first file found
        blob = blobs[0]
        content = blob.download_as_bytes()
        file_name = blob.name.split("/")[-1]

        # Determine content type
        if file_name.endswith(".csv"):
            content_type = "text/csv"
        elif file_name.endswith((".xlsx", ".xls")):
            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            content_type = "application/octet-stream"

        # Return file
        response = make_response(content)
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
        response.headers["Content-Type"] = content_type
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        return cors_response({"error": str(e)}, 500)


"""
Deployment command (Production):
gcloud functions deploy get_master_file
  --runtime python310
  --trigger-http
  --entry-point get_master_file
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_get_master_file
  --runtime python310
  --trigger-http
  --entry-point get_master_file
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=development
"""
