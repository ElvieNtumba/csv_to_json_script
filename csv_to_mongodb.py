import csv
import json
from pymongo import MongoClient

# --- CONFIGURATION ---
CSV_FILE_PATH = "/home/elvie/Documents/activeteamsdatascript/ActiveTeams spreadsheet - All People.csv"  # path to your CSV file
MONGO_URI = "mongodb+srv://activeteams:helloactiveteams@active-teams.ykghvqr.mongodb.net/"  # or your Atlas URI
DB_NAME = "testing-data-active-teams"
COLLECTION_NAME = "people"
# ----------------------

def transform_values(row):
    """Transforms specific field values according to given rules."""
    new_row = {}
    for key, value in row.items():
        if isinstance(value, str):
            # Normalize key spacing and apply conversions (case-insensitive)
            key_lower = key.strip().lower()

            # Match by key name instead of text in value
            if key_lower == "leader @12":
                key = "Leader @1"
            elif key_lower == "leader @144":
                key = "Leader @12"
            elif key_lower == "leader @ 1728":
                key = "Leader @144"

        new_row[key] = value
        
        # if "Leader @1728" not in new_row:
        #     new_row["Leader @1728"] = ""
    
    return new_row

def csv_to_json(csv_file_path):
    """Reads CSV and converts each row to a transformed dict (JSON-style)."""
    json_list = []
    with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            transformed_row = transform_values(row)
            json_list.append(transformed_row)
    return json_list

def upload_to_mongodb(data, uri, db_name, collection_name, batch_size=500):
    """Uploads list of JSON documents to MongoDB in batches."""
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    if not data:
        print("No data found in CSV!")
        return

    total = len(data)
    for i in range(0, total, batch_size):
        batch = data[i:i+batch_size]
        result = collection.insert_many(batch)
        print(f"Inserted {len(result.inserted_ids)} docs ({i + len(batch)}/{total})")

    print(f"Successfully inserted {total} documents into '{db_name}.{collection_name}'.")

def main():
    print("Reading CSV file...")
    data = csv_to_json(CSV_FILE_PATH)

    print("Uploading data to MongoDB...")
    upload_to_mongodb(data, MONGO_URI, DB_NAME, COLLECTION_NAME)

    print("Done!")

if __name__ == "__main__":
    main()