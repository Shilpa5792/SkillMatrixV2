"""
Insert 2 rows into EmployeeCertificates for employee IDs 4 and 5
"""

import psycopg2
import db_utils


def insert_employee_certificates():
    """Insert 2 test rows for employees 4 and 5"""
    
    with db_utils.get_db_connection() as conn:
        with conn.cursor() as cur:
            
            # Insert 2 rows for employee IDs 4 and 5
            cur.execute("""
                INSERT INTO "EmployeeCertificates" 
                (employee_id, certificate_id, issued_date, expiry_date, created_at, updated_at)
                VALUES 
                    (4, '1', '2024-01-15', '2027-01-15', NOW(), NOW()),
                    (5, '2', '2024-06-01', '2026-06-01', NOW(), NOW())
                RETURNING id, employee_id, certificate_id;
            """)
            
            records = cur.fetchall()
            conn.commit()
            
            print(f"✓ Inserted {len(records)} records")
            for rec in records:
                print(f"  ID: {rec[0]}, Employee: {rec[1]}, Certificate: {rec[2]}")


if __name__ == "__main__":
    try:
        insert_employee_certificates()
        print("\n✓ Done! Test API at http://127.0.0.1:8080/")
    except Exception as e:
        print(f"✗ Error: {e}")