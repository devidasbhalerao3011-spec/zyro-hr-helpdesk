# Zyro Dynamics — Intelligent HR Help Desk (RAG)

A Streamlit HR-policy chatbot built with LangChain, FAISS, MMR retrieval and an LLM. It answers only from the supplied Zyro Dynamics HR policy PDFs, displays source/page citations, and uses a standard refusal when the documents do not support an answer.

## Architecture

1. **Load** the 11 PDFs from `data/hr_policies/` with page metadata.
2. **Chunk** pages with recursive splitting (default: 1,000 characters, 150 overlap).
3. **Embed** chunks with OpenAI `text-embedding-3-small`.
4. **Index** embeddings in a persistent FAISS vector store (fingerprinted to detect changed source documents/settings).
5. **Retrieve** relevant chunks using maximal marginal relevance (MMR).
6. **Generate** a grounded response with Groq, OpenAI, or Gemini.
7. **Cite** the source PDF and one-based page number; refuse when the evidence is insufficient.

## Project structure

```text
.
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── data/hr_policies/       # Add the 11 competition PDFs here
├── notebooks/              # Starter-notebook integration notes
├── src/
│   ├── document_loader.py
│   ├── text_splitter.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── rag_chain.py
│   ├── guardrails.py
│   ├── citations.py
│   └── submission.py
└── tests/
```

## 1. Install

Use Python 3.10 or 3.11.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

On Windows, copy `.env.example` to `.env` manually if `cp` is unavailable.

## 2. Add the competition data

Download the official 11 HR policy PDFs from the Kaggle competition and place them in:

```text
data/hr_policies/
```

Keep the original PDF filenames. The supplied ZIP did not contain the actual PDFs or the official starter notebook, so those must be added from the competition Data section. The loader checks for exactly 11 PDFs by default.

## 3. Configure API keys

Edit `.env`. Example using Groq for generation:

```dotenv
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your_groq_key

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_openai_key
```

**Important:** Groq is the chat model provider in this example, but embeddings still use OpenAI. Therefore both `GROQ_API_KEY` and `OPENAI_API_KEY` are required. Alternatively choose `LLM_PROVIDER=openai` or `LLM_PROVIDER=gemini` and provide the matching key. Never commit API keys.

Optional LangSmith tracing:

```dotenv
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=zyro-rag-challenge
```

## 4. Run the chatbot

```bash
streamlit run app.py
```

The first run extracts the PDFs, creates chunks, embeds them and builds the FAISS index. Later runs reuse the index when its fingerprint matches the documents and embedding configuration.

## 5. Run tests

```bash
pytest -q
```

## 6. Competition submission (20 rows)

Use the official competition starter notebook's **Copy & Edit** workflow. It is authoritative for the dataset path, actual question IDs, test questions and submission cell.

Export the notebook's 20 questions to a CSV with:
- `question_id`
- one of `question`, `question_text`, or `query`

Then run from the project root:

```bash
python -m src.submission --questions competition_questions.csv --output submission.csv
```

The script requires exactly 20 unique IDs and creates exactly two columns: `question_id,answer`. It preserves input order. Do not fabricate IDs or replace the official notebook's required workflow; if the competition instructs you to run its final submission cell, do that and use this script only if its input format is compatible.

## 7. Deploy on Streamlit Community Cloud

1. Push this project to a GitHub repository.
2. Add the 11 policy PDFs through a hosting approach permitted by the competition (the PDFs are excluded from Git by default).
3. Set the app entry point to `app.py`.
4. Add secrets in Streamlit Cloud's **App settings → Secrets**, for example:

```toml
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = "..."
OPENAI_API_KEY = "..."
EMBEDDING_PROVIDER = "openai"
EMBEDDING_MODEL = "text-embedding-3-small"
EXPECTED_PDF_COUNT = "11"
```

5. Deploy and test one question covered by the policies and one unrelated question.

## Important limitations / final checks

- The uploaded ZIP contains the application scaffold but **not** the 11 PDF files, official competition notebook, hidden questions or sample submission. Add/download these from Kaggle before running.
- OCR for image-only/scanned PDFs is not included. The loader expects selectable PDF text.
- The out-of-scope guardrail combines retrieved-evidence checks with a strict grounded-answer prompt. Test it against the competition's out-of-scope examples; retrieval alone is not proof that a question is in scope.
- Validate the final `submission.csv` against the competition's sample submission before upload.
