from langchain_openai import OpenAIEmbeddings

def get_embeddings(settings):
    provider = settings.embedding_provider
    if provider == "openai":
        return OpenAIEmbeddings(model=settings.embedding_model)
    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER={provider!r}. "
        "This baseline supports 'openai'; add another LangChain embedding adapter if needed."
    )
