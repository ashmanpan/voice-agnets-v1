"""
Migration script to add language support columns
Adds preferred_language to contacts table
(language column already exists in calls table)
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://voiceagent:voiceagent@db:5432/voiceagent")
engine = create_engine(DATABASE_URL)

def add_language_columns():
    with engine.connect() as conn:
        # Add preferred_language to contacts if it doesn't exist
        print("Adding preferred_language column to contacts table...")
        try:
            conn.execute(text("""
                ALTER TABLE contacts
                ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) DEFAULT 'en';
            """))
            conn.commit()
            print("✅ Added preferred_language column to contacts")
        except Exception as e:
            print(f"⚠️  Error adding preferred_language: {e}")

        # Verify language column exists in calls (should already be there)
        print("\nVerifying language column in calls table...")
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'calls' AND column_name = 'language';
        """))
        if result.fetchone():
            print("✅ Language column exists in calls table")
        else:
            print("Adding language column to calls table...")
            try:
                conn.execute(text("""
                    ALTER TABLE calls
                    ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
                """))
                conn.commit()
                print("✅ Added language column to calls")
            except Exception as e:
                print(f"⚠️  Error adding language column: {e}")

        # Verify columns were added
        print("\n=== Verification ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'contacts' AND column_name = 'preferred_language';
        """))
        row = result.fetchone()
        if row:
            print(f"✅ contacts.preferred_language: {row[1]} (default: {row[2]})")

        result = conn.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'calls' AND column_name = 'language';
        """))
        row = result.fetchone()
        if row:
            print(f"✅ calls.language: {row[1]} (default: {row[2]})")

        print("\n✅ Language support migration complete!")

if __name__ == "__main__":
    add_language_columns()
