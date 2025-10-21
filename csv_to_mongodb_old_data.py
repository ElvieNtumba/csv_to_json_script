import csv
import json
from pymongo import MongoClient
import re 

# --- CONFIGURATION ---
CSV_FILE_PATH = "/home/elvie/Documents/activeteamsdatascript/active-teams-db.People.csv"  # path to your CSV file
MONGO_URI = "mongodb+srv://activeteams:helloactiveteams@active-teams.ykghvqr.mongodb.net/"  # or your Atlas URI
DB_NAME = "old-active-teams-data"
COLLECTION_NAME = "people"
# ----------------------

def csv_to_json(csv_file_path):
    """Reads CSV and converts each row to a dict (JSON-style)."""
    json_list = []
    with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            json_list.append(row)
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