from models import engine, Base, Interaction, HCP
from sqlalchemy import text

def sync_schema():
    with engine.connect() as conn:
        print("Checking for missing columns in 'interactions' table...")
        columns_to_add = [
            ("time", "VARCHAR"),
            ("attendees", "VARCHAR"),
            ("topics_discussed", "TEXT"),
            ("samples_distributed", "JSONB" if "postgresql" in str(engine.url) else "JSON")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE interactions ADD COLUMN {col_name} {col_type}"))
                print(f"Added column {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"Column {col_name} already exists.")
                else:
                    print(f"Error adding {col_name}: {e}")
        
        conn.commit()
    print("Schema sync complete.")

if __name__ == "__main__":
    sync_schema()
