import pandas as pd
from db_utils import get_db_connection
from datetime import datetime

# ============================================
# STEP 1: Put your CSV file path here
# ============================================
CSV_FILE_PATH = "C:/Users/Pelleti.reddy/Downloads/INFOLDER_Master_Certificates.csv"


def create_sequence():
    """Create sequence for MasterCertificate if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if sequence exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_class 
                WHERE relname = 'mastercertificate_id_seq'
            )
        """)
        exists = cursor.fetchone()[0]
        
        if not exists:
            print("Creating sequence for MasterCertificate...")
            
            # Get current max ID
            cursor.execute('SELECT COALESCE(MAX(id::integer), 0) as max_id FROM "MasterCertificate"')
            max_id = cursor.fetchone()[0]
            
            # Create sequence starting from max_id + 1
            cursor.execute(f"""
                CREATE SEQUENCE mastercertificate_id_seq
                START WITH {max_id + 1}
                INCREMENT BY 1
            """)
            
            conn.commit()
            print(f"✓ Sequence created! Starting from {max_id + 1}")
        else:
            print("✓ Sequence already exists")
    
    finally:
        cursor.close()
        conn.close()


def load_certificates():
    """Load certificates from CSV to database"""
    
    print("Starting to load certificates...")
    print("-" * 50)
    
    # Verify schema
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_schema()")
    current_schema = cursor.fetchone()[0]
    print(f"✓ Using schema: {current_schema}")
    cursor.close()
    conn.close()
    print()
    
    # Create sequence first
    create_sequence()
    print()
    
    # Read CSV file
    df = pd.read_csv(CSV_FILE_PATH)
    print(f"Total records found in CSV: {len(df)}")
    print()
    
    # ============================================
    # CHECK 1: Rename columns to match database
    # ============================================
    print("Checking and mapping columns...")
    
    # Map your CSV columns to database columns
    column_mapping = {
        'Certification Provider': 'certprovider',
        'Certification Name': 'certname',
        'Certification Level': 'certlevel',
        'Valid Years': 'validyears'
    }
    
    # Check if all required columns exist in CSV
    missing = []
    for csv_col in column_mapping.keys():
        if csv_col not in df.columns:
            missing.append(csv_col)
    
    if missing:
        print(f"ERROR: CSV is missing these columns: {missing}")
        print(f"Your CSV has: {df.columns.tolist()}")
        return
    
    # Rename columns to match database
    df = df.rename(columns=column_mapping)
    
    print("✓ All required columns are present!")
    print()
    
    # ============================================
    # CHECK 2: Check for duplicates in database
    # ============================================
    print("Checking for duplicates in database...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all existing certificates from database
    cursor.execute("""
        SELECT certprovider, certname, certlevel 
        FROM "MasterCertificate"
    """)
    existing_certs = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Count duplicates
    duplicate_count = 0
    new_records = []
    
    for index, row in df.iterrows():
        # Check if this certificate already exists in database
        is_duplicate = False
        for existing in existing_certs:
            if (existing[0] == row['certprovider'] and 
                existing[1] == row['certname'] and 
                existing[2] == row['certlevel']):
                is_duplicate = True
                break
        
        if is_duplicate:
            duplicate_count += 1
            print(f"  Duplicate found: {row['certprovider']} - {row['certname']} ({row['certlevel']})")
        else:
            new_records.append(row)
    
    print(f"\nTotal duplicates found: {duplicate_count}")
    print(f"New records to insert: {len(new_records)}")
    print()
    
    # If no new records, stop here
    if len(new_records) == 0:
        print("No new records to insert. All certificates already exist!")
        return
    
    # ============================================
    # INSERT: Add new records to database
    # ============================================
    print("Inserting new records into database...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    inserted_count = 0
    
    try:
        for row in new_records:
            # Insert query - use sequence to generate id
            query = """
                INSERT INTO "MasterCertificate" 
                (id, certprovider, certname, certlevel, validyears, isactive, created_at, updated_at)
                VALUES (nextval('mastercertificate_id_seq'), %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Current timestamp
            now = datetime.now()
            
            # Data to insert
            data = (
                row['certprovider'],
                row['certname'],
                row['certlevel'],
                int(row['validyears']),
                True,
                now,
                now
            )
            
            # Execute insert
            cursor.execute(query, data)
            inserted_count += 1
        
        # Commit all inserts
        conn.commit()
        print(f"✓ Successfully inserted {inserted_count} new certificates!")
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise e
    
    finally:
        cursor.close()
        conn.close()
    
    # ============================================
    # VERIFY: Check if data was inserted
    # ============================================
    print("\nVerifying data in database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM "MasterCertificate"')
    total = cursor.fetchone()[0]
    print(f"Total certificates in database: {total}")
    
    # Show first 5 records
    cursor.execute('SELECT * FROM "MasterCertificate" ORDER BY id DESC LIMIT 5')
    records = cursor.fetchall()
    print("\nLast 5 inserted records:")
    for rec in records:
        print(f"  ID: {rec[0]} | {rec[1]} | {rec[2]} | {rec[3]}")
    
    cursor.close()
    conn.close()
    
    print("-" * 50)
    print("Done!")


# Run the function
if __name__ == "__main__":
    load_certificates()