import hashlib
import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from src.embeddings import get_embeddings

def _fingerprint(chunks, settings):
    digest = hashlib.sha256()
    digest.update(settings.embedding_provider.encode())
    digest.update(settings.embedding_model.encode())
    for doc in chunks:
        digest.update(doc.metadata.get("source", "").encode())
        digest.update(str(doc.metadata.get("page", "")).encode())
        digest.update(doc.page_content.encode())
    return digest.hexdigest()

def get_vector_store(chunks, settings):
    index_dir = Path(settings.index_dir)
    manifest_path = index_dir / "manifest.json"
    fingerprint = _fingerprint(chunks, settings)
    embeddings = get_embeddings(settings)

    if index_dir.exists() and manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("fingerprint") == fingerprint:
                return FAISS.load_local(
                    str(index_dir), embeddings, allow_dangerous_deserialization=True
                )
        except Exception:
            # Invalid or incompatible local cache: rebuild below.
            pass

    store = FAISS.from_documents(chunks, embeddings)
    index_dir.mkdir(parents=True, exist_ok=True)
    store.save_local(str(index_dir))
    manifest_path.write_text(
        json.dumps({"fingerprint": fingerprint}, indent=2), encoding="utf-8"
    )
    return store
