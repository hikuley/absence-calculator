import csv
import os
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import AbsencePeriod
from datetime import datetime

# Path to the CSV file
CSV_FILE_PATH = os.environ.get('CSV_FILE_PATH', 'data/absence_periods.csv')

def migrate_data():
    """Migrate data from CSV file to PostgreSQL database"""
    print(f"Starting migration from {CSV_FILE_PATH} to PostgreSQL database...")
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            print(f"CSV file not found at {CSV_FILE_PATH}")
            return
        
        # Read data from CSV file
        absence_periods = []
        with open(CSV_FILE_PATH, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                absence_periods.append(row)
        
        print(f"Read {len(absence_periods)} periods from CSV file")
        
        # Check if data already exists in the database
        existing_count = db.query(AbsencePeriod).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} records. Clearing existing data for fresh migration.")
            # Delete all existing records
            db.query(AbsencePeriod).delete()
            db.commit()
        
        # Insert data into database
        for period in absence_periods:
            db_period = AbsencePeriod.from_dict(period)
            db.add(db_period)
        
        # Commit changes
        db.commit()
        print(f"Successfully migrated {len(absence_periods)} periods to PostgreSQL database")
    
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    
    finally:
        # Close database session
        db.close()

if __name__ == "__main__":
    migrate_data()
