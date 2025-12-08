import os
import smtplib
import logging
import base64
import json
import time
from flask import jsonify, make_response
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"❌ config.json not found at: {CONFIG_PATH}")

with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

SMTP_SERVER = CONFIG.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = CONFIG.get("SMTP_PORT", 587)
SENDER_EMAIL = CONFIG["SMTP_EMAIL"]
SENDER_PASSWORD = CONFIG["SMTP_PASS"]


def cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def send_mail(request):
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    try:
        data = request.get_json(silent=True)
        if not data:
            logger.error("❌ Missing JSON body in request")
            return cors_response({"error": "Missing JSON body"}, 400)

        to_email = data.get("to")
        subject = data.get("subject")
        body = data.get("body")
        attachments = data.get("attachments", [])  # list of base64 encoded files

        missing_fields = [
            field for field in ["to", "subject", "body"] if not data.get(field)
        ]
        if missing_fields:
            logger.error("❌ Missing required fields: %s", ", ".join(missing_fields))
            logger.error("Data:", data)
            return cors_response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400
            )

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))  # Supports HTML body

        # Attach files if provided
        for attachment in attachments:
            filename = attachment.get("filename")
            filedata = attachment.get("content")

            if not (filename and filedata):
                continue

            file_bytes = base64.b64decode(filedata)
            part = MIMEApplication(file_bytes)
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            msg.attach(part)

        # Time the actual send
        start_time = time.time()

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        duration = time.time() - start_time
        logger.info(f"📤 Email sent to {to_email} in {duration:.2f} seconds")

        return cors_response({"success": True, "message": f"Email successfully"})

    except Exception as e:
        logger.exception("❌ Failed to send email")
        return cors_response({"error": str(e)}, 500)



"""
Production Deployment command:
gcloud functions deploy send_mail 
    --runtime python310 
    --trigger-http 
    --entry-point send_mail 
    --service-account training-project-419308@appspot.gserviceaccount.com 
    --allow-unauthenticated 
    --no-gen2 
    --region asia-south1 
    --set-env-vars ENV=production   
"""
"""
Developement Deployment command:
gcloud functions deploy dev_send_mail 
    --runtime python310 
    --trigger-http 
    --entry-point send_mail 
    --service-account training-project-419308@appspot.gserviceaccount.com 
    --allow-unauthenticated 
    --no-gen2 
    --region asia-south1 
    --set-env-vars ENV=development   
"""
"""
Local testing command:
    functions-framework --target=send_mail --port=8084 --debug 
"""
