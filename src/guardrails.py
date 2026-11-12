REFUSAL = (
    "I’m sorry, but the supplied HR policy documents do not provide enough "
    "information to answer this question reliably. Please contact HR for clarification."
)

def has_retrieved_evidence(question: str, documents) -> bool:
    """Basic empty-context guard only; relevance and sufficiency are judged in the grounded prompt."""
    return bool(question.strip()) and bool(documents) and any(
        doc.page_content.strip() for doc in documents
    )
