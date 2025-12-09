"""
Final production-ready script to split MasterCertificate into 3 tables
Table 1: MasterCertificateProvider
Table 2: ProviderCertificateMapping  
Table 3: MasterCertificate (certificates only)
"""
import sys
from db_utils import get_db_connection

def print_now(msg):
    """Print immediately without buffering"""
    print(msg)
    sys.stdout.flush()

def check_current_state(cursor):
    """Check what tables and columns currently exist"""
    print_now("Checking current database state...")
    print_now("="*60)
    
    # Check which tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'skill-matrix-dev'
        AND table_name IN ('MasterCertificate', 'MasterCertificateProvider', 'ProviderCertificateMapping')
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print_now("\nExisting tables:")
    for table in existing_tables:
        print_now(f"  ✓ {table}")
    
    if 'MasterCertificate' in existing_tables:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'skill-matrix-dev'
            AND table_name = 'MasterCertificate'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        print_now(f"\nMasterCertificate columns: {', '.join(columns)}")
        
        cursor.execute('SELECT COUNT(*) FROM "MasterCertificate"')
        count = cursor.fetchone()[0]
        print_now(f"MasterCertificate has {count} records")
    
    print_now("="*60)
    return existing_tables, columns if 'MasterCertificate' in existing_tables else []

def create_provider_table(cursor):
    """Table 1: MasterCertificateProvider"""
    print_now("\nStep 1: Creating MasterCertificateProvider table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "MasterCertificateProvider" (
            id SERIAL PRIMARY KEY,
            certprovider VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        INSERT INTO "MasterCertificateProvider" (certprovider, created_at, updated_at)
        SELECT DISTINCT 
            certprovider,
            MIN(created_at),
            MAX(updated_at)
        FROM "MasterCertificate"
        GROUP BY certprovider
        ON CONFLICT (certprovider) DO NOTHING
    """)
    
    print_now(f"✓ Created with {cursor.rowcount} providers")

def create_certificate_table(cursor):
    """Table 3: New MasterCertificate (certificates only)"""
    print_now("\nStep 2: Creating new MasterCertificate table (certificates)...")
    
    # Rename old table temporarily
    cursor.execute("""
        ALTER TABLE "MasterCertificate" 
        RENAME TO "MasterCertificate_OLD"
    """)
    print_now("  - Renamed old table to MasterCertificate_OLD")
    
    # Create new MasterCertificate table
    cursor.execute("""
        CREATE TABLE "MasterCertificate" (
            id SERIAL PRIMARY KEY,
            certname VARCHAR(500) NOT NULL,
            certlevel VARCHAR(100) NOT NULL,
            validyears INTEGER DEFAULT 0,
            isactive BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(certname, certlevel)
        )
    """)
    
    cursor.execute("""
        INSERT INTO "MasterCertificate" (certname, certlevel, validyears, isactive, created_at, updated_at)
        SELECT DISTINCT 
            certname,
            certlevel,
            validyears,
            isactive,
            MIN(created_at),
            MAX(updated_at)
        FROM "MasterCertificate_OLD"
        GROUP BY certname, certlevel, validyears, isactive
        ON CONFLICT (certname, certlevel) DO NOTHING
    """)
    
    print_now(f"✓ Created with {cursor.rowcount} certificates")

def create_mapping_table(cursor):
    """Table 2: ProviderCertificateMapping"""
    print_now("\nStep 3: Creating ProviderCertificateMapping table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "ProviderCertificateMapping" (
            id SERIAL PRIMARY KEY,
            provider_id INTEGER NOT NULL,
            certificate_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (provider_id) REFERENCES "MasterCertificateProvider"(id) ON DELETE CASCADE,
            FOREIGN KEY (certificate_id) REFERENCES "MasterCertificate"(id) ON DELETE CASCADE,
            UNIQUE(provider_id, certificate_id)
        )
    """)
    
    cursor.execute("""
        INSERT INTO "ProviderCertificateMapping" (provider_id, certificate_id, created_at, updated_at)
        SELECT DISTINCT
            mcp.id as provider_id,
            mc.id as certificate_id,
            old.created_at,
            old.updated_at
        FROM "MasterCertificate_OLD" old
        JOIN "MasterCertificateProvider" mcp ON old.certprovider = mcp.certprovider
        JOIN "MasterCertificate" mc ON old.certname = mc.certname 
            AND old.certlevel = mc.certlevel
        ON CONFLICT (provider_id, certificate_id) DO NOTHING
    """)
    
    print_now(f"✓ Created with {cursor.rowcount} mappings")

def create_indexes(cursor):
    """Create indexes for better performance"""
    print_now("\nStep 4: Creating indexes...")
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mapping_provider 
        ON "ProviderCertificateMapping"(provider_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mapping_certificate 
        ON "ProviderCertificateMapping"(certificate_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_certificate_level 
        ON "MasterCertificate"(certlevel)
    """)
    
    print_now("✓ Indexes created")

def drop_old_table(cursor):
    """Drop the temporary old table"""
    print_now("\nStep 5: Dropping old table...")
    cursor.execute('DROP TABLE IF EXISTS "MasterCertificate_OLD" CASCADE')
    print_now("✓ MasterCertificate_OLD dropped")

def verify_migration(cursor):
    """Verify the migration"""
    print_now("\n" + "="*60)
    print_now("VERIFICATION - FINAL 3 TABLE STRUCTURE")
    print_now("="*60)
    
    # Count records
    cursor.execute('SELECT COUNT(*) FROM "MasterCertificateProvider"')
    provider_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM "MasterCertificate"')
    cert_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM "ProviderCertificateMapping"')
    mapping_count = cursor.fetchone()[0]
    
    print_now(f"\nTable 1 - MasterCertificateProvider: {provider_count} providers")
    print_now(f"Table 2 - ProviderCertificateMapping: {mapping_count} mappings")
    print_now(f"Table 3 - MasterCertificate: {cert_count} certificates")
    
    # Show sample data
    print_now("\n=== Sample Providers ===")
    cursor.execute("""
        SELECT id, certprovider 
        FROM "MasterCertificateProvider" 
        ORDER BY id LIMIT 5
    """)
    for row in cursor.fetchall():
        print_now(f"  {row[0]} | {row[1]}")
    
    print_now("\n=== Sample Certificates ===")
    cursor.execute("""
        SELECT id, certname, certlevel 
        FROM "MasterCertificate" 
        ORDER BY id LIMIT 5
    """)
    for row in cursor.fetchall():
        print_now(f"  {row[0]} | {row[1]} | {row[2]}")
    
    print_now("\n=== Sample Mappings (with JOIN) ===")
    cursor.execute("""
        SELECT 
            pcm.id,
            mcp.certprovider,
            mc.certname,
            mc.certlevel
        FROM "ProviderCertificateMapping" pcm
        JOIN "MasterCertificateProvider" mcp ON pcm.provider_id = mcp.id
        JOIN "MasterCertificate" mc ON pcm.certificate_id = mc.id
        ORDER BY pcm.id LIMIT 5
    """)
    for row in cursor.fetchall():
        print_now(f"  {row[0]} | {row[1]} → {row[2]} ({row[3]})")
    
    print_now("\n Migration completed successfully!")

def main():
    """Main function"""
    print_now("="*60)
    print_now("SPLIT MasterCertificate INTO 3 TABLES")
    print_now("="*60)
    print_now("")
    
    print_now("Connecting to database...")
    try:
        conn = get_db_connection()
        print_now("✓ Connected successfully\n")
    except Exception as e:
        print_now(f" Connection failed: {e}")
        return
    
    cursor = conn.cursor()
    
    try:
        # Check current state
        existing_tables, columns = check_current_state(cursor)
        
        # Check if migration already done
        if 'MasterCertificateProvider' in existing_tables and 'ProviderCertificateMapping' in existing_tables:
            print_now("\n  Migration appears to be already completed!")
            response = input("Do you want to recreate? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print_now("Cancelled.")
                return
        
        # Check if old MasterCertificate has the right columns
        if 'certprovider' not in columns:
            print_now("\n ERROR: MasterCertificate doesn't have 'certprovider' column!")
            print_now("It looks like the table was already modified.")
            print_now("Please restore from backup or check the database state.")
            return
        
        # Step 1: Create MasterCertificateProvider
        create_provider_table(cursor)
        conn.commit()
        
        # Step 2: Create new MasterCertificate (certificates only)
        create_certificate_table(cursor)
        conn.commit()
        
        # Step 3: Create ProviderCertificateMapping
        create_mapping_table(cursor)
        conn.commit()
        
        # Step 4: Create Indexes
        create_indexes(cursor)
        conn.commit()
        
        # Step 5: Drop old table
        response = input("\n  Drop the old table (MasterCertificate_OLD)? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            drop_old_table(cursor)
            conn.commit()
        
        # Step 6: Verify
        verify_migration(cursor)
        
    except Exception as e:
        print_now(f"\n ERROR: {e}")
        print_now("\nRolling back changes...")
        conn.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        conn.close()
        print_now("\nDatabase connection closed.")

if __name__ == "__main__":
    main()