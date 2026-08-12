from bson import ObjectId

from app.mongo_client import build_vector_search_pipeline


def test_pipeline_structure():
    doc_id = ObjectId()
    pipe = build_vector_search_pipeline(doc_id, [0.1] * 384, top_k=4)
    stage = pipe[0]["$vectorSearch"]
    assert stage["index"] == "vector_index"
    assert stage["path"] == "embedding"
    assert stage.get("numDimensions") is None
    assert stage["queryVector"] == [0.1] * 384
    assert stage["limit"] == 4
    assert stage["numCandidates"] == 40
    assert stage["filter"] == {"document_id": doc_id}
    assert pipe[1] == {"$project": {"_id": 0, "text": 1, "page_number": 1}}