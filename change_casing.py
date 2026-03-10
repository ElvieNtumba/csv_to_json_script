# rename_organization_to_Organization.py
from pymongo import MongoClient
from pymongo.operations import UpdateOne
import time
from typing import Set


def rename_organization_field(
    mongodb_uri: str,
    database_name: str,
    old_field: str = "organization",
    new_field: str = "Organization",
    dry_run: bool = True,
    batch_size: int = 1000
):
    """
    Renames the field 'organization' → 'Organization' in all documents
    across relevant collections — without changing the values themselves.
    
    - Only affects documents that actually have the 'organization' field
    - Preserves original case of the values
    - Excludes the same collections as before
    - Safe dry-run mode by default
    """
    EXCLUDE_COLLECTIONS: Set[str] = {"organizations", "OrgConfig"}

    try:
        client = MongoClient(mongodb_uri)
        db = client[database_name]
        
        print(f"Connected to database: {database_name}")
        print(f"Renaming field: {old_field} → {new_field}")
        print(f"Values will NOT be uppercased — original case is preserved")
        print(f"Dry run: {'YES — simulation only' if dry_run else 'NO — WILL MODIFY DATA'}")
        print(f"Excluded collections: {', '.join(sorted(EXCLUDE_COLLECTIONS))}")
        print("-" * 70)

        collections = [
            name for name in db.list_collection_names()
            if name not in EXCLUDE_COLLECTIONS
            and not name.startswith("system.")
        ]

        if not collections:
            print("No collections found to process.")
            return

        total_updated = 0
        total_collections = len(collections)

        for i, coll_name in enumerate(collections, 1):
            collection = db[coll_name]
            
            # Count documents that have the old field (any type)
            to_update = collection.count_documents({old_field: {"$exists": True}})

            if to_update == 0:
                print(f"[{i:2d}/{total_collections}] {coll_name:.<38} → no '{old_field}' fields to rename")
                continue

            print(f"[{i:2d}/{total_collections}] {coll_name:.<38} → {to_update:,} documents will have field renamed")

            if dry_run:
                continue

            # ── Real rename in batches ──────────────────────────────────
            updated_count = 0
            last_id = None

            while True:
                match = {old_field: {"$exists": True}}

                if last_id is not None:
                    match["_id"] = {"$gt": last_id}

                pipeline = [
                    {"$match": match},
                    {"$sort": {"_id": 1}},
                    {"$limit": batch_size},
                    {"$project": {"_id": 1}}
                ]

                batch = list(collection.aggregate(pipeline))
                if not batch:
                    break

                operations = [
                    UpdateOne(
                        {"_id": doc["_id"]},
                        {"$rename": {old_field: new_field}}
                    )
                    for doc in batch
                ]

                if operations:
                    result = collection.bulk_write(operations)
                    updated_count += result.modified_count
                    print(f" → batch renamed {result.modified_count:,} (total: {updated_count:,})", flush=True)

                last_id = batch[-1]["_id"]
                time.sleep(0.04)  # gentle on the server

            print(f" Finished {coll_name} — {updated_count:,} documents updated")
            total_updated += updated_count

        print("-" * 70)
        
        if dry_run:
            print("Dry run finished. No changes were made.")
        else:
            print(f"Completed. Total documents with field renamed: {total_updated:,}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    # ┌───────────────────────────────────────────────────────────────┐
    # │           ← CHANGE THESE VALUES AS NEEDED →                   │
    # └───────────────────────────────────────────────────────────────┘
    MONGODB_URI = "mongodb+srv://activeteams:helloactiveteams@active-teams.ykghvqr.mongodb.net/"
    DATABASE    = "test-data-active-teams"

    rename_organization_field(
        mongodb_uri   = MONGODB_URI,
        database_name = DATABASE,
        old_field     = "organization",
        new_field     = "Organization",
        dry_run       = False,          # ← already set to False in your version
        batch_size    = 1500
    )