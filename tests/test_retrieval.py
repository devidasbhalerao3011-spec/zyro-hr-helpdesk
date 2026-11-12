from src.text_splitter import split_documents
from langchain_core.documents import Document

def test_chunks_are_nonempty_and_keep_metadata():
    docs = [Document(page_content="Policy sentence. " * 200, metadata={"source": "leave.pdf", "page": 2})]
    chunks = split_documents(docs, chunk_size=200, chunk_overlap=30)
    assert chunks
    assert all(chunk.page_content.strip() for chunk in chunks)
    assert all(chunk.metadata["source"] == "leave.pdf" for chunk in chunks)
    assert all(chunk.metadata["page"] == 2 for chunk in chunks)
