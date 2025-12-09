"""
Rename tables to match desired naming convention
Run this once, then delete this file
"""
import sys
from db_utils import get_db_connection

def print_now(msg):
    """Print immediately without buffering"""
    print(msg)
    sys.stdout.flush()

def rename_tables(cursor):
    """Rename the tables"""
    print_now("Renaming tables...")
    print_now("="*60)
    
    # Rename CertificationProvider to MasterCertificateProvider
    try:
        cursor.execute("""
            ALTER TABLE "CertificationProvider" 
            RENAME TO "MasterCertificateProvider"
        """)
        print_now("✓ CertificationProvider → MasterCertificateProvider")
    except Exception as e:
        print_now(f"  ⚠️  CertificationProvider rename skipped: {e}")
    
    # Rename Certificate to MasterCertificate
    try:
        cursor.execute("""
            ALTER TABLE "Certificate" 
            RENAME TO "MasterCertificate"
        """)
        print_now("✓ Certificate → MasterCertificate")
    except Exception as e:
        print_now(f"  ⚠️  Certificate rename skipped: {e}")
    
    print_now("="*60)
    print_now("\n✅ Tables renamed successfully!")
    print_now("\nFinal structure:")
    print_now("  Table 1: MasterCertificateProvider")
    print_now("  Table 2: ProviderCertificateMapping")
    print_now("  Table 3: MasterCertificate")

def main():
    """Main function"""
    print_now("="*60)
    print_now("RENAME TABLES")
    print_now("="*60)
    print_now("")
    
    response = input("This will rename:\n"
                    "  CertificationProvider → MasterCertificateProvider\n"
                    "  Certificate → MasterCertificate\n"
                    "Proceed? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print_now("Cancelled.")
        return
    
    print_now("\nConnecting to database...")
    try:
        conn = get_db_connection()
        print_now("✓ Connected\n")
    except Exception as e:
        print_now(f"❌ Connection failed: {e}")
        return
    
    cursor = conn.cursor()
    
    try:
        rename_tables(cursor)
        conn.commit()
        print_now("\n✅ Done! You can now delete this script.")
        
    except Exception as e:
        print_now(f"\n❌ ERROR: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        conn.close()
        print_now("\nDatabase connection closed.")

if __name__ == "__main__":
    main()