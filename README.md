# Zyro Dynamics HR Help Desk — RAG project

## 1. Project structure

```text
zyro-hr-helpdesk/
├── app.py
├── rag_pipeline.py
├── generate_submission.py
├── requirements.txt
├── .env.example
├── test.csv
└── data/
    └── hr_policies/
        └── (11 HR policy PDF files)
```

## 2. Requirements
- Python 3.10 or 3.11 recommended
- A Groq API key
- Internet access for first-time model/dependency downloads

## 3. Setup on Windows PowerShell

Open PowerShell in this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder with your Groq API key. Never share or upload this key.

Put the 11 policy PDFs in `data/hr_policies/`.

## 4. Run the chatbot

```powershell
python -m streamlit run app.py
```

The app normally opens at http://localhost:8501.

## 5. Generate the competition CSV

Copy the competition's `test.csv` into this project root. The file must include `question_id` and a question column named `question`, `query`, or `prompt`.

```powershell
python generate_submission.py
```

It creates `submission.csv` with `question_id,answer`. Check that it has exactly 20 rows and matches the competition's sample submission format before uploading.

## Notes
- PDFs are loaded and split into overlapping chunks.
- Hugging Face `all-MiniLM-L6-v2` creates local embeddings.
- FAISS stores vectors and MMR retrieves diverse relevant chunks.
- Groq's Llama model generates answers using retrieved excerpts only.
- The similarity threshold is a starting point, not a guarantee. Test in-scope and out-of-scope examples and adjust it based on validation.
- This project does not guarantee a competition score. Verify every answer against the source policy PDFs.
