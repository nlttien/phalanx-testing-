import csv
import json
import os
import urllib.request
import urllib.parse

def extract_sheet_id_from_url(url):
    start = url.find('/d/') + 3
    end = url.find('/edit')
    if start != -1 and end != -1:
        return url[start:end]
    return None

def read_google_sheet_csv(sheet_id, range_name='Sheet1!A:D'):
    """
    Read Google Sheets data using CSV export URL.
    This method works for public sheets without authentication.
    """
    # Construct the CSV export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    try:
        # Download the CSV data
        response = urllib.request.urlopen(csv_url)
        csv_data = response.read().decode('utf-8')
        
        # Parse CSV data
        csv_reader = csv.reader(csv_data.splitlines())
        rows = list(csv_reader)
        
        return rows
    except Exception as e:
        print(f"Error reading Google Sheets: {e}")
        return None

def extract_data_from_rows(rows):
    if len(rows) < 2:
        print("Sheet doesn't have enough rows")
        return None
    
    data_row = rows[1] if len(rows) > 1 else None
    
    if not data_row or len(data_row) < 4:
        print("Row 2 doesn't have enough columns")
        return None
    
    data = {
        "User Name": data_row[0] if len(data_row) > 0 else "",
        "Email": data_row[1] if len(data_row) > 1 else "",
        "Subject": data_row[2] if len(data_row) > 2 else "",
        "Content": data_row[3] if len(data_row) > 3 else ""
    }
    
    return data

def create_json_file(data, filename):
    try:
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"JSON file created: {filename}")
        return True
    except Exception as e:
        print(f"Error creating JSON file: {e}")
        return False

def create_csv_file(data, filename):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["User Name", "Email", "Subject", "Content"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            
            writer.writerow(data)
        
        print(f"CSV file created: {filename}")
        return True
    except Exception as e:
        print(f"Error creating CSV file: {e}")
        return False

def main():
    sheet_url = "https://docs.google.com/spreadsheets/d/1lNsIW2A1gmurYZ-DJt65xuX_yEsxyvoqPx84Q2B8rEM/edit?gid=0#gid=0"
    
    print("Starting Google Sheets data extraction...")
    print(f"Source URL: {sheet_url}")
    
    # Extract sheet ID from URL
    sheet_id = extract_sheet_id_from_url(sheet_url)
    if not sheet_id:
        print("Error: Could not extract sheet ID from URL")
        return False
    
    print(f"Sheet ID: {sheet_id}")
    
    # Read data from Google Sheets
    rows = read_google_sheet_csv(sheet_id)
    if not rows:
        print("Error: Could not read data from Google Sheets")
        return False
    
    print(f"Read {len(rows)} rows from the sheet")
    
    # Extract the specific data we need
    data = extract_data_from_rows(rows)
    if not data:
        print("Error: Could not extract required data from sheet")
        return False
    
    print("Extracted data:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    # Create output files
    json_filename = "data/basic_row.json"
    csv_filename = "data/basic_row.csv"
    
    # Create JSON file
    json_success = create_json_file(data, json_filename)
    
    # Create CSV file  
    csv_success = create_csv_file(data, csv_filename)
    
    if json_success and csv_success:
        print("\nSuccessfully created both output files:")
        print(f"  - {json_filename}")
        print(f"  - {csv_filename}")
        return True
    else:
        print("Error: Failed to create one or more output files")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nScript completed successfully!")
    else:
        print("\nScript completed with errors!")
