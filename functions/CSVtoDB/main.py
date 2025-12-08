import logging
import os
import pandas as pd
import tempfile
import json
import requests
from google.cloud import storage
from db.database import create_database, load_config
from datetime import datetime
from db.models import MasterSkills, MasterCertificate  # ✅ new model import

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
config = load_config()


def process_csv_to_db(event, context):
    bucket_name = event.get("bucket")
    file_name = event.get("name")
    print(f"Triggered by file: {file_name} in bucket: {bucket_name}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    master_type = "Unknown"
    new_data_inserted = False
    error_message = None
    total_rows = valid_rows = faulty_count = 0
    df = df_valid = faulty_rows = None

    # Validate file type and location
    if not (
        file_name
        and file_name.startswith("INFOLDER/")
        and file_name.endswith((".csv", ".xlsx", ".xls"))
    ):
        print("Not a supported file or not in INFOLDER/, skipping. " + file_name)
        return

    if "Master_Skills" in file_name or "Master_Certificates" in file_name:
        print(f"⏭️ Skipping master file '{file_name}' to prevent re-trigger.")
        return

    is_skill = "Skill" in file_name
    is_certificate = "Certificate" in file_name

    if not (is_skill or is_certificate):
        print(f"⏭️ Skipping file '{file_name}' — not Skill or Certificate.")
        return

    client = storage.Client()
    tmp_file = None
    session = None

    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_name)

        if not blob.exists():
            raise FileNotFoundError(f"File not found in bucket: {file_name}")

        suffix = ".xlsx" if file_name.endswith((".xlsx", ".xls")) else ".csv"
        tmp_file = tempfile.mktemp(suffix=suffix)
        blob.download_to_filename(tmp_file)

        # Read file
        df = pd.read_csv(tmp_file) if suffix == ".csv" else pd.read_excel(tmp_file)

        if df.empty:
            raise ValueError("File is empty.")

        # Setup DB session
        engine, SessionLocal = create_database()
        session = SessionLocal()

        if is_skill:
            master_type = "Skills"
            print("Processing Skill CSV → MasterSkills table")

            key_fields = ["Category", "Sub-Category", "Sub-Sub-Category", "Tools"]
            df[key_fields] = (
                df[key_fields].fillna("").astype(str).apply(lambda x: x.str.strip())
            )

            # 1️⃣ Missing values (empty or NaN in any key field)
            missing_mask = df[key_fields].isna().any(axis=1) | (
                df[key_fields] == ""
            ).any(axis=1)
            missing_rows = df[missing_mask]

            # 2️⃣ Duplicates (duplicate combos of Category/Sub/Tools)
            duplicate_mask = df.duplicated(subset=key_fields, keep=False)
            duplicate_rows = df[duplicate_mask]

            # Combine faulty rows (union of both)
            faulty_rows = pd.concat([missing_rows, duplicate_rows]).drop_duplicates()

            # Valid rows = rows that are not faulty
            df_valid = df[~df.index.isin(faulty_rows.index)]

            df_valid[["L1", "L2", "L3"]] = (
                df_valid[["L1", "L2", "L3"]]
                .fillna("")
                .astype(str)
                .apply(lambda x: x.str.strip())
            )

            print(
                f"⚙️ Found {len(missing_rows)} missing-value rows and {len(duplicate_rows)} duplicate rows."
            )
            print(
                f"⚙️ Total faulty rows: {len(faulty_rows)}, valid rows: {len(df_valid)}"
            )

            if df_valid.empty:
                raise ValueError("No valid skill rows found.")
            with session.begin():

                session.query(MasterSkills).delete()

                skills_data = [
                    MasterSkills(
                        category=row["Category"],
                        subcategory=row["Sub-Category"],
                        subsubcategory=row["Sub-Sub-Category"],
                        tools=row["Tools"],
                        L1=row.get("L1"),
                        L2=row.get("L2"),
                        L3=row.get("L3"),
                    )
                    for _, row in df_valid.iterrows()
                ]

                session.add_all(skills_data)
                new_data_inserted = True
                print(f"✅ Inserted {len(skills_data)} skill rows.")

        elif is_certificate:
            master_type = "Certificates"
            print("Processing Certificate CSV → MasterCertificate table")

            key_fields = [
                "Certification Provider",
                "Certification Name",
                "Certification Level",
                "Valid Years",
                "isActive",
            ]
            df[key_fields] = (
                df[key_fields].fillna("").astype(str).apply(lambda x: x.str.strip())
            )
            df["Valid Years"] = (
                pd.to_numeric(df["Valid Years"], errors="coerce").fillna(0).astype(int)
            )

            # 1️⃣ Missing values (blank or NaN in required fields)
            required_fields = ["Certification Provider", "Certification Name"]
            missing_mask = df[required_fields].isna().any(axis=1) | (
                df[required_fields] == ""
            ).any(axis=1)
            missing_rows = df[missing_mask]

            # 2️⃣ Duplicate records (same provider + name + level)
            dup_subset = [
                "Certification Provider",
                "Certification Name",
                "Certification Level",
            ]
            duplicate_mask = df.duplicated(subset=dup_subset, keep=False)
            duplicate_rows = df[duplicate_mask]

            # Combine faulty rows (union of both)
            faulty_rows = pd.concat([missing_rows, duplicate_rows]).drop_duplicates()

            # Valid rows = rows not in faulty set
            df_valid = df[~df.index.isin(faulty_rows.index)]
            print(
                f"⚙️ Found {len(missing_rows)} missing-value rows and {len(duplicate_rows)} duplicate rows."
            )
            print(
                f"⚙️ Total faulty rows: {len(faulty_rows)}, valid rows: {len(df_valid)}"
            )

            if df_valid.empty:
                raise ValueError("No valid certificate rows found.")
            with session.begin():
                session.query(MasterCertificate).delete()

                cert_data = [
                    MasterCertificate(
                        certProvider=row["Certification Provider"],
                        certName=row["Certification Name"],
                        certLevel=row.get("Certification Level"),
                        validYears=row.get("Valid Years", 0),
                        isActive=row.get("isActive", 0),
                    )
                    for _, row in df_valid.iterrows()
                ]

                session.add_all(cert_data)
                new_data_inserted = True
                print(f"✅ Inserted {len(cert_data)} certificate rows.")

        # File renaming and version management
        if new_data_inserted:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            master_prefix = "Master_Skills" if is_skill else "Master_Certificates"
            destination_blob_name = f"INFOLDER/{master_prefix}{suffix}"
            backup_blob_name = f"Master_File_Backup/{master_prefix}_{ts}_backup{suffix}"

            # Reference blobs
            previous_master_blob = bucket.blob(destination_blob_name)
            uploaded_blob = blob  # original uploaded file

            # Backup previous master if exists
            if previous_master_blob.exists():
                # Clean old backups for this master type
                for old in bucket.list_blobs(
                    prefix=f"Master_File_Backup/{master_prefix}_"
                ):
                    old.delete()

                # Copy previous master to backup folder
                bucket.copy_blob(previous_master_blob, bucket, backup_blob_name)
                previous_master_blob.delete()
                print(
                    f"🕒 Previous master backed up → gs://{bucket_name}/{backup_blob_name}"
                )

            # Move uploaded file to master location
            bucket.copy_blob(uploaded_blob, bucket, destination_blob_name)
            uploaded_blob.delete()

            print(f"✅ New master saved → gs://{bucket_name}/{destination_blob_name}")

    except Exception as e:
        error_message = str(e)
        print(e)
        logger.exception("❌ Error processing CSV/Excel to DB")

    finally:
        # Close session
        if session:
            session.close()

        # Remove temp file
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)

        # Save faulty rows
        if faulty_rows is not None and not faulty_rows.empty:
            try:
                faulty_json = faulty_rows.where(pd.notnull(faulty_rows), None).to_dict(
                    orient="records"
                )
                safe_name = file_name.replace("/", "_").replace("\\", "_")
                faulty_blob_name = f"faulty_records/{safe_name}_faulty.json"
                faulty_blob = client.bucket(bucket_name).blob(faulty_blob_name)
                faulty_blob.upload_from_string(
                    json.dumps(faulty_json, indent=2), content_type="application/json"
                )
                logger.warning(
                    f"⚠️ Stored {len(faulty_rows)} faulty rows → gs://{bucket_name}/{faulty_blob_name}"
                )
            except Exception:
                logger.exception(f"❌ Failed to upload faulty records for {file_name}")

        # Send notification mail (always)
        try:
            base_url = config.get("BASE_URL")
            to_email = config.get("TO_EMAIL")
            SEND_EMAIL_URL = f"{base_url}send_mail"
            if base_url and to_email:
                endpoint = SEND_EMAIL_URL
                total_rows = len(df) if df is not None else 0
                valid_rows = len(df_valid) if df_valid is not None else 0
                faulty_count = len(faulty_rows) if faulty_rows is not None else 0

                if error_message:
                    subject = f"🚨 Master {master_type} Processing Error"
                    body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height:1.5; color:#333;">
                        <h2 style="color:#d9534f;">🚨 Error Processing Master {master_type}</h2>
                        <p>Dear Admin,</p>
                        <p>An error occurred while processing the <strong>{master_type}</strong> file.</p>
                        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>File Name</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px;">{file_name}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Error</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px; color:#d9534f;">{error_message}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Timestamp</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px;">{timestamp}</td>
                            </tr>
                        </table>
                        <p>Regards,<br/>Skill Matrix Automation System</p>
                    </body>
                    </html>
                    """
                elif new_data_inserted:
                    subject = f"✅ Master {master_type} File Processed Successfully"
                    body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height:1.5; color:#333;">
                        <h2 style="color:#28a745;">✅ Master {master_type} Processed Successfully</h2>
                        <p>Dear Admin,</p>
                        <p>The <strong>{master_type}</strong> master file has been successfully processed.</p>
                        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>File Name</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px;">{file_name}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Total Rows</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px;">{total_rows}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Valid Inserted Rows</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px; color:#28a745;">{valid_rows}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Faulty Rows</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px; color:#ffc107;">{faulty_count}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Processed At</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px;">{timestamp}</td>
                            </tr>
                        </table>
                        <p>Regards,<br/>Skill Matrix Automation System</p>
                    </body>
                    </html>
                    """
                else:
                    subject = f"⚠️ Master {master_type} File Processing Skipped"
                    body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height:1.5; color:#333;">
                        <h2 style="color:#ffc107;">⚠️ Master {master_type} File Skipped</h2>
                        <p>Dear Admin,</p>
                        <p>The <strong>{master_type}</strong> file did not insert any valid data.</p>
                        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>File Name</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px;">{file_name}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Total Rows</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px;">{total_rows}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Faulty Rows</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px; color:#ffc107;">{faulty_count}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px;"><strong>Processed At</strong></td>
                                <td style="border: 1px solid #ccc; padding: 8px;">{timestamp}</td>
                            </tr>
                        </table>
                        <p>Regards,<br/>Skill Matrix Automation System</p>
                    </body>
                    </html>
                    """

                resp = requests.post(
                    endpoint,
                    json={"to": to_email, "subject": subject, "body": body},
                    timeout=10,
                )
                if resp.status_code == 200:
                    print(f"📧 Mail sent successfully to {to_email}")
                else:
                    print(f"⚠️ Failed to send mail ({resp.status_code}) → {resp.text}")
            else:
                print("⚠️ Missing BASE_URL or TO_EMAIL in config.json")
        except Exception:
            logger.exception("❌ Failed to send notification email")


"""
Production Deploy Command:
gcloud functions deploy csv_to_db_bucket_trigger
  --runtime python310 
  --trigger-bucket skill_matrix 
  --entry-point process_csv_to_db 
  --service-account training-project-419308@appspot.gserviceaccount.com 
  --region asia-south1 
  --no-gen2 
  --memory 512MB 
  --timeout 540s
  --set-env-vars ENV=production
"""

"""
Development Deploy Command:
gcloud functions deploy dev_csv_to_db_bucket_trigger
  --runtime python310 
  --trigger-bucket dev_skill_matrix 
  --entry-point process_csv_to_db 
  --service-account training-project-419308@appspot.gserviceaccount.com 
  --region asia-south1 
  --no-gen2 
  --memory 512MB 
  --timeout 540s
  --set-env-vars ENV=development
"""
