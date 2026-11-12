from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    pdf_dir: Path
    index_dir: Path
    expected_pdf_count: int
    chunk_size: int
    chunk_overlap: int
    retrieval_k: int
    fetch_k: int
    lambda_mult: float
    embedding_provider: str
    embedding_model: str
    llm_provider: str
    llm_model: str
    temperature: float

def get_settings() -> Settings:
    return Settings(
        pdf_dir=Path(os.getenv("HR_PDF_DIR", "data/hr_policies")),
        index_dir=Path(os.getenv("FAISS_INDEX_DIR", "faiss_index")),
        expected_pdf_count=int(os.getenv("EXPECTED_PDF_COUNT", "11")),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
        retrieval_k=int(os.getenv("RETRIEVAL_K", "5")),
        fetch_k=int(os.getenv("FETCH_K", "15")),
        lambda_mult=float(os.getenv("MMR_LAMBDA", "0.5")),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "openai").lower(),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        llm_provider=os.getenv("LLM_PROVIDER", "groq").lower(),
        llm_model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
    )
