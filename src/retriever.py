def get_retriever(vector_store, settings):
    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": settings.retrieval_k,
            "fetch_k": settings.fetch_k,
            "lambda_mult": settings.lambda_mult,
        },
    )
