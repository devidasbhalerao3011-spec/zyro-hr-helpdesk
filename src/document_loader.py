from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader

def load_policy_documents(pdf_dir: Path, expected_count: int = 11):
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory does not exist: {pdf_dir}")
    files = sorted(pdf_dir.rglob("*.pdf"))
    if not files:
        raise FileNotFoundError(f"No PDF files found in {pdf_dir}")
    if expected_count and len(files) != expected_count:
        raise ValueError(
            f"Expected {expected_count} policy PDFs, found {len(files)} in {pdf_dir}. "
            "Check the competition dataset path and file layout."
        )

    documents = []
    failures = []
    for pdf_path in files:
        try:
            pages = PyPDFLoader(str(pdf_path)).load()
            for page_doc in pages:
                text = (page_doc.page_content or "").strip()
                if not text:
                    continue
                metadata = dict(page_doc.metadata)
                metadata["source"] = str(pdf_path.relative_to(pdf_dir))
                metadata["page"] = int(metadata.get("page", 0)) + 1
                documents.append(type(page_doc)(page_content=text, metadata=metadata))
        except Exception as exc:
            failures.append(f"{pdf_path.name}: {exc}")

    if failures:
        raise RuntimeError("One or more PDFs could not be parsed: " + " | ".join(failures))
    if not documents:
        raise ValueError("PDF files were found, but no selectable text was extracted.")
    print(f"Processed {len(files)} PDF files and extracted {len(documents)} non-empty pages.")
    return documents
