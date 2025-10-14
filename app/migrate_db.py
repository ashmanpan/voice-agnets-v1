"""
Database Migration Script
Adds new columns and tables for scheduler and call analysis
"""
from models import Base, engine
from sqlalchemy import text

def migrate():
    print("Running database migration...")

    with engine.connect() as conn:
        # Add retry columns to calls table if they don't exist
        try:
            conn.execute(text("""
                ALTER TABLE calls
                ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3,
                ADD COLUMN IF NOT EXISTS retry_on_no_answer BOOLEAN DEFAULT TRUE;
            """))
            conn.commit()
            print("✓ Added retry columns to calls table")
        except Exception as e:
            print(f"  Retry columns may already exist: {e}")

    # Create all tables (this will create call_analysis if it doesn't exist)
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Created/verified all tables including call_analysis")
    except Exception as e:
        print(f"Error creating tables: {e}")

    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate()
