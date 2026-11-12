def format_citations(documents):
    """Return de-duplicated, display-ready source/page references."""
    citations = []
    seen = set()
    for doc in documents:
        source = doc.metadata.get("source")
        page = doc.metadata.get("page")
        if source is None:
            continue
        key = (source, page)
        if key not in seen:
            seen.add(key)
            citations.append({"source": source, "page": page})
    return citations
