import csv
import os
import uuid

# Define file paths
source_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'home_task', 'absence_periods.csv')
target_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'absence_periods.csv')

def update_csv_with_ids():
    """
    Copy data from home_task/absence_periods.csv to absence_periods.csv with random UUIDs
    """
    print(f"Source CSV: {source_csv_path}")
    print(f"Target CSV: {target_csv_path}")
    
    # Check if source file exists
    if not os.path.exists(source_csv_path):
        print(f"Source file not found: {source_csv_path}")
        return False
    
    try:
        # Read data from source CSV
        rows = []
        with open(source_csv_path, 'r') as source_file:
            reader = csv.DictReader(source_file)
            field_mapping = {}
            
            # Check if the source CSV has inbound_date/outbound_date or start_date/end_date
            if 'inbound_date' in reader.fieldnames and 'outbound_date' in reader.fieldnames:
                field_mapping = {'inbound_date': 'start_date', 'outbound_date': 'end_date'}
                print("Using inbound_date/outbound_date fields from source CSV")
            else:
                field_mapping = {'start_date': 'start_date', 'end_date': 'end_date'}
                print("Using start_date/end_date fields from source CSV")
            
            # Read all rows
            for row in reader:
                # Map fields to start_date/end_date
                start_date = row.get(field_mapping.get('start_date', 'start_date')) or row.get('inbound_date')
                end_date = row.get(field_mapping.get('end_date', 'end_date')) or row.get('outbound_date')
                
                if start_date and end_date:
                    rows.append({
                        'id': str(uuid.uuid4()),
                        'start_date': start_date,
                        'end_date': end_date
                    })
        
        # Write data to target CSV
        with open(target_csv_path, 'w', newline='') as target_file:
            fieldnames = ['id', 'start_date', 'end_date']
            writer = csv.DictWriter(target_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        
        print(f"Successfully copied {len(rows)} rows from source to target CSV with random UUIDs")
        return True
    
    except Exception as e:
        print(f"Error updating CSV: {e}")
        return False

if __name__ == "__main__":
    update_csv_with_ids()
