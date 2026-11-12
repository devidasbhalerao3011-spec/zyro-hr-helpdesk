from langchain_core.documents import Document
from src.guardrails import has_retrieved_evidence

def test_empty_retrieval_is_not_evidence():
    assert not has_retrieved_evidence("How much leave?", [])

def test_nonempty_retrieval_is_evidence_candidate():
    docs = [Document(page_content="Annual leave policy.", metadata={"source": "leave.pdf", "page": 1})]
    assert has_retrieved_evidence("How much leave?", docs)
