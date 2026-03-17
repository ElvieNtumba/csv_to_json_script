# add_organization_field_to_all_collections.py
from pymongo import MongoClient
from pymongo.operations import UpdateOne
from typing import Optional
import time


def add_organization_to_all_collections(
    mongodb_uri: str,
    database_name: str,
    organization_value: str = "Active Church",
    field_name: str = "Organization",
    dry_run: bool = True,
    batch_size: int = 1000
):
    """
    Adds an 'organization' field to every document in every collection
    (except excluded ones).
    """
    EXCLUDE_COLLECTIONS = {"organizations", "OrgConfig"}

    try:
        client = MongoClient(mongodb_uri)
        db = client[database_name]

        print(f"Connected to database: {database_name}")
        print(f"Target field     : {field_name}")
        print(f"Value to set     : {organization_value}")
        print(f"Dry run mode     : {'YES (no changes)' if dry_run else 'NO — WILL MODIFY DATA'}")
        print("-" * 60)

        collections = db.list_collection_names()
        if not collections:
            print("No collections found in the database.")
            return

        total_docs_updated = 0
        total_collections = len(collections)

        for i, collection_name in enumerate(collections, 1):
            if collection_name in EXCLUDE_COLLECTIONS:
                print(f"[{i}/{total_collections}] {collection_name:.<35} → SKIPPED (excluded)")
                continue

            collection = db[collection_name]

            # Count how many documents still miss the field
            missing_count = collection.count_documents({field_name: {"$exists": False}})

            if missing_count == 0:
                print(f"[{i}/{total_collections}] {collection_name:.<35} already has {field_name} in all docs")
                continue

            print(f"[{i}/{total_collections}] {collection_name:.<35} → {missing_count:,} documents need update")

            if dry_run:
                continue

            # Batch update
            updated_in_coll = 0
            last_id = None

            while True:
                pipeline = [
                    {"$match": {field_name: {"$exists": False}}},
                    {"$sort": {"_id": 1}},
                    {"$limit": batch_size}
                ]

                if last_id is not None:
                    pipeline[0]["$match"]["_id"] = {"$gt": last_id}

                batch = list(collection.aggregate(pipeline))
                if not batch:
                    break

                # Prepare bulk operations
                operations = [
                    UpdateOne(
                        filter={"_id": doc["_id"]},
                        update={"$set": {field_name: organization_value}},
                        upsert=False
                    )
                    for doc in batch
                ]

                if operations:
                    result = collection.bulk_write(operations)
                    updated_in_coll += result.modified_count
                    print(f"  → batch updated {result.modified_count} docs", end="", flush=True)
                    print(f"  (total: {updated_in_coll:,})")

                if batch:  # safety check
                    last_id = batch[-1]["_id"]

                time.sleep(0.05)  # gentle on the server

            total_docs_updated += updated_in_coll
            print(f"  Finished {collection_name} — {updated_in_coll:,} documents updated")
            print("-" * 60)

        if dry_run:
            print("Dry run complete. No documents were modified.")
        else:
            print(f"Update finished. Total documents updated: {total_docs_updated:,}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client.close()


if __name__ == "__main__":
    # ┌───────────────────────────────────────────────────────────────┐
    # │                  ← CHANGE THESE VALUES →                      │
    # └───────────────────────────────────────────────────────────────┘
    MONGODB_URI = "mongodb+srv://activeteams:helloactiveteams@active-teams.ykghvqr.mongodb.net/"
    DATABASE = "test-data-active-teams"
    ORG_VALUE = "Active Church"
    FIELD_NAME = "Organization"

    add_organization_to_all_collections(
        mongodb_uri=MONGODB_URI,
        database_name=DATABASE,
        organization_value=ORG_VALUE,
        field_name=FIELD_NAME,
        dry_run=False,           # Change to True if you want to preview again
        batch_size=2000
    )