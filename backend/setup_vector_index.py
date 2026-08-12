INDEX_NAME = "vector_index"
INDEX_DEFINITION = {
    "fields": [
        {"type": "vector", "path": "embedding", "numDimensions": 384, "similarity": "cosine"},
        {"type": "filter", "path": "document_id"},
    ]
}


def _to_api_definition(definition: dict) -> dict:
    fields = {}
    for field in definition["fields"]:
        if field["type"] == "vector":
            fields[field["path"]] = {
                "type": "knnVector",
                "dimensions": field["numDimensions"],
                "similarity": field["similarity"],
            }
        else:
            fields[field["path"]] = {"type": field["type"]}
    return {"mappings": {"dynamic": False, "fields": fields}}


def create_vector_index(uri: str, db_name: str) -> str:
    from pymongo import MongoClient

    with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
        client.admin.command("ping")
        collection = client[db_name]["chunks"]
        existing = collection.list_search_indexes()
        for idx in existing:
            if idx.get("name") == INDEX_NAME:
                return "already exists"
        collection.create_search_index({"name": INDEX_NAME, "definition": _to_api_definition(INDEX_DEFINITION)})
        return "created"


if __name__ == "__main__":
    import os
    import sys

    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB_NAME", "documentor_db")
    if not uri:
        sys.exit("MONGODB_URI is required")
    try:
        result = create_vector_index(uri, db_name)
        print(f"[setup_vector_index] vector_index {result} on {db_name}.chunks")
        print("Manual alternative (Atlas UI): Cluster > Search > Create Search Index >")
        print("JSON Editor with the fields definition from this script.")
    except Exception as exc:
        sys.exit(f"[setup_vector_index] failed: {exc}")
