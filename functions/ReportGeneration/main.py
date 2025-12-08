import os
import pandas as pd
import tempfile
import json
import csv
import requests
import base64
from google.cloud import storage
from datetime import datetime
from db.database import create_database, load_config
from db.models import Employee, EmployeeSkills
from flask import jsonify, make_response
import logging

logger = logging.getLogger(__name__)
config = load_config()

EXCLUDED_DEPARTMENTS = ["General and Administration", "Sales and Marketing"]


def cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def generate_employee_skills_report(request):
    """
    HTTP endpoint to generate Employee Skills report, save CSV, upload to GCS, and email it.
    """
    if request.method == "OPTIONS":
        return cors_response("", 204)

    bucket_name = config.get("GCP_BUCKET_NAME")
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # 1️⃣ Get latest Master Employee file
        blobs = list(bucket.list_blobs(prefix="Master_Employee_List/"))
        actual_files = [b for b in blobs if not b.name.endswith("/") and b.size > 0]

        if not actual_files:
            return cors_response(
                {"error": "No Master Employee files found in bucket."}, 404
            )

        latest_blob = max(actual_files, key=lambda b: b.updated)
        suffix = os.path.splitext(latest_blob.name)[1]
        tmp_file = tempfile.mktemp(suffix=suffix)
        latest_blob.download_to_filename(tmp_file)
        logger.info(f"Downloaded latest Master Employee file: {latest_blob.name}")

        # 2️⃣ Read Excel/CSV and ensure Employee Number is string
        df_emp = (
            pd.read_csv(tmp_file, dtype={"Employee Number": str})
            if suffix == ".csv"
            else pd.read_excel(tmp_file, dtype={"Employee Number": str})
        )
        df_emp = df_emp[
            (~df_emp["Department"].isin(EXCLUDED_DEPARTMENTS))
            & (df_emp["Ignore"].fillna("").str.strip().str.lower() != "yes")
        ]

        # 3️⃣ Setup DB session
        engine, SessionLocal = create_database()
        session = SessionLocal()

        # 4️⃣ Fetch Employee and EmployeeSkills data
        skills_df = pd.read_sql(session.query(EmployeeSkills).statement, session.bind)
        employee_df = pd.read_sql(session.query(Employee).statement, session.bind)

        # Normalize and align datatypes
        employee_df["id"] = employee_df["id"].astype(str).str.strip()
        skills_df["empId"] = skills_df["empId"].astype(str).str.strip()

        employee_df["email"] = employee_df["email"].astype(str).str.strip().str.lower()
        employee_df["managerEmail"] = (
            employee_df["managerEmail"].astype(str).str.strip().str.lower()
        )
        skills_df["approvedByEmail"] = (
            skills_df["approvedByEmail"].astype(str).str.strip().str.lower()
        )

        # 5️⃣ Compute skills summary per employee
        skill_summary = (
            skills_df.groupby("empId")
            .agg(
                Total_Skills=("id", "count"),
                L3_Skills=("levelSelected", lambda x: sum(x == "L3")),
            )
            .reset_index()
        )

        # 6️⃣ Merge skill summary into employee_df
        employee_df = employee_df.merge(
            skill_summary, how="left", left_on="id", right_on="empId"
        )
        employee_df[["Total_Skills", "L3_Skills"]] = employee_df[
            ["Total_Skills", "L3_Skills"]
        ].fillna(0)

        mgr_pending = (
            skills_df[skills_df["approvalStatus"].str.lower() == "pending"]
            .groupby("approvedByEmail")
            .size()
            .reset_index(name="Pending_Count")
        )

        def skill_matrix_status(row):
            print(row)
            if pd.isna(row["Total_Skills"]):
                return "Not logged in"
            if row["Total_Skills"] >= 1:
                return "Completed"
            return "Not completed"

        employee_df["Skill Matrix Updated"] = employee_df.apply(
            skill_matrix_status, axis=1
        )
        employee_df["L3 Skills"] = employee_df["L3_Skills"].apply(
            lambda x: "Yes" if x >= 1 else "No"
        )

        def get_pending_status(row):
            email = row["email"]
            # not a manager
            if email not in employee_df["managerEmail"].values:
                return ""
            pending = mgr_pending[mgr_pending["approvedByEmail"] == email]
            if not pending.empty and pending["Pending_Count"].iloc[0] >= 1:
                return "Yes"
            return "No"

        employee_df["PendingApprovalRequest"] = employee_df.apply(
            get_pending_status, axis=1
        )

        # 9️⃣ Merge employee_df with df_emp to include Department, Sub Department, etc.
        df_emp["Work Email"] = df_emp["Work Email"].astype(str).str.strip().str.lower()
        employee_df["email"] = employee_df["email"].astype(str).str.strip().str.lower()

        report = df_emp.merge(
            employee_df[
                [
                    "email",
                    "Skill Matrix Updated",
                    "L3 Skills",
                    "PendingApprovalRequest",
                ]
            ],
            left_on="Work Email",
            right_on="email",
            how="left",
        )

        # 10️⃣ Final cleanup and formatting
        report["Employee Number"] = report["Employee Number"].astype(str).str.zfill(6)
        report["Skill Matrix Updated"] = (
            report["Skill Matrix Updated"].replace("", pd.NA).fillna("Not Logged In")
        )

        report = report[
            [
                "Employee Number",
                "Full Name",
                "Work Email",
                "Department",
                "Sub Department",
                "Skill Matrix Updated",
                "L3 Skills",
                "PendingApprovalRequest",
            ]
        ]

        # 11️⃣ Save report locally
        report_file = f"/tmp/Report_{timestamp}.csv"
        report.to_csv(report_file, index=False, quoting=csv.QUOTE_NONNUMERIC)
        logger.info(f"✅ Report saved locally: {report_file}")

        # 12️⃣ Upload to GCS
        generated_blob_name = f"Generated_report/Report_{timestamp}.csv"
        generated_blob = bucket.blob(generated_blob_name)
        generated_blob.upload_from_filename(report_file)
        logger.info(
            f"✅ Report uploaded to bucket: gs://{bucket_name}/{generated_blob_name}"
        )

        # 13️⃣ Send Email with attachment
        base_url = config.get("BASE_URL")
        to_email = config.get("TO_EMAIL")
        SEND_EMAIL_URL = f"{base_url}send_mail"

        if base_url and to_email:
            with open(report_file, "rb") as f:
                file_content = f.read()
            attachment_base64 = base64.b64encode(file_content).decode("utf-8")

            body = f"""
            <html>
                <body>
                    <p>Dear Admin,</p>
                    <p>The Employee Skills report has been generated successfully.</p>
                    <p>Regards,<br/>Skill Matrix Automation System</p>
                </body>
            </html>
            """

            resp = requests.post(
                SEND_EMAIL_URL,
                json={
                    "to": to_email,
                    "subject": f"Employee Skills Report - {timestamp}",
                    "body": body,
                    "attachments": [
                        {
                            "filename": f"Report_{timestamp}.csv",
                            "content": attachment_base64,
                        }
                    ],
                },
                timeout=20,
            )

            if resp.status_code == 200:
                logger.info(f"📧 Report sent successfully to {to_email}")
            else:
                logger.warning(
                    f"⚠️ Failed to send report ({resp.status_code}) → {resp.text}"
                )

        return cors_response(
            {"success": True, "message": f"Report generated and sent to {to_email}"}
        )

    except Exception as e:
        logger.exception("❌ Failed to generate Employee Skills report")
        return cors_response({"error": str(e)}, 500)

    finally:
        if "session" in locals():
            session.close()
        if "tmp_file" in locals() and os.path.exists(tmp_file):
            os.remove(tmp_file)


"""
Deployment command (Production):
gcloud functions deploy generate_employee_skills_report
  --runtime python310
  --trigger-http
  --entry-point generate_employee_skills_report
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=production
"""
"""
Deployment command (Development):
gcloud functions deploy dev_generate_employee_skills_report
  --runtime python310
  --trigger-http
  --entry-point generate_employee_skills_report
  --service-account training-project-419308@appspot.gserviceaccount.com
  --allow-unauthenticated
  --no-gen2
  --region asia-south1
  --set-env-vars ENV=development
"""
"""
Local testing command:
functions-framework --target=generate_employee_skills_report --port=8084 --debug 
"""
