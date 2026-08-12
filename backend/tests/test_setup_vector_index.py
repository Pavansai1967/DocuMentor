import setup_vector_index


def test_index_definition_shape():
    definition = setup_vector_index.INDEX_DEFINITION
    fields = definition["fields"]
    vector_field = next(f for f in fields if f["type"] == "vector")
    assert vector_field["path"] == "embedding"
    assert vector_field["numDimensions"] == 384
    assert vector_field["similarity"] == "cosine"
    assert any(f["type"] == "filter" and f["path"] == "document_id" for f in fields)
