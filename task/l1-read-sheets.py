import os
import pandas as pd
import json

def extract_sheet_id_from_url(url):
    start = url.find('/d/') + 3
    end = url.find('/edit')
    if start != -1 and end != -1:
        return url[start:end]
    return None

def read_google_sheet_with_pandas(sheet_id):
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        return None

def extract_specific_data_with_pandas(df):
    if df is None or df.empty:
        return None
    
    if len(df) < 1:
        return None
    
    try:
        row_data = df.iloc[0]  
        
        data = {
            "User Name": str(row_data.iloc[0]) if pd.notna(row_data.iloc[0]) and len(row_data) > 0 else "",
            "Email": str(row_data.iloc[1]) if pd.notna(row_data.iloc[1]) and len(row_data) > 1 else "",
            "Subject": str(row_data.iloc[2]) if pd.notna(row_data.iloc[2]) and len(row_data) > 2 else "",
            "Content": str(row_data.iloc[3]) if pd.notna(row_data.iloc[3]) and len(row_data) > 3 else ""
        }
        
        return data
    except Exception as e:
        return None

def create_output_files_with_pandas(data):
    if not data:
        return False, False
    
    os.makedirs("data", exist_ok=True)
    
    df = pd.DataFrame([data])
    
    try:
        csv_filename = "data/basic_row.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        csv_success = True
    except Exception as e:
        csv_success = False
    
    try:
        json_filename = "data/basic_row.json"
        json_data = df.iloc[0].to_dict() 
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        json_success = True
    except Exception as e:
        json_success = False
    
    return json_success, csv_success

def main():
    sheet_url = "https://docs.google.com/spreadsheets/d/1lNsIW2A1gmurYZ-DJt65xuX_yEsxyvoqPx84Q2B8rEM/edit?gid=0#gid=0"
    
    sheet_id = extract_sheet_id_from_url(sheet_url)
    if not sheet_id:
        return False
    
    
    # Read data using pandas
    df = read_google_sheet_with_pandas(sheet_id)
    if df is None:
        return False
    
    # Extract the specific data we need
    data = extract_specific_data_with_pandas(df)
    if not data:
        return False
    
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    # Create output files using pandas
    json_success, csv_success = create_output_files_with_pandas(data)
    
    if json_success and csv_success:
        print("\nSuccessfully created both output files:")
        print("  - data/basic_row.json")
        print("  - data/basic_row.csv")
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
