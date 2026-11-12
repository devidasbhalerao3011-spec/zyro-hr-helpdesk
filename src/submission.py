import argparse
from pathlib import Path
import pandas as pd

from config import get_settings
from src.document_loader import load_policy_documents
from src.text_splitter import split_documents
from src.vector_store import get_vector_store
from src.retriever import get_retriever
from src.rag_chain import build_rag_pipeline, answer_question

def generate_submission(input_csv: str, output_csv: str = "submission.csv"):
    """Input CSV must come from the competition starter workflow; IDs are never generated here."""
    questions = pd.read_csv(input_csv)
    required = {"question_id"}
    if not required.issubset(questions.columns):
        raise ValueError("Input CSV must contain the competition-provided question_id column.")
    question_col = next(
        (name for name in ("question", "question_text", "query") if name in questions.columns),
        None,
    )
    if question_col is None:
        raise ValueError("Input CSV must also contain question, question_text, or query.")

    if len(questions) != 20:
        raise ValueError(f"Expected exactly 20 competition questions; found {len(questions)}.")
    if questions["question_id"].isna().any() or questions["question_id"].duplicated().any():
        raise ValueError("Question IDs must be present and unique.")
    if questions[question_col].isna().any():
        raise ValueError("One or more competition questions are empty.")

    settings = get_settings()
    docs = load_policy_documents(settings.pdf_dir, settings.expected_pdf_count)
    chunks = split_documents(docs, settings.chunk_size, settings.chunk_overlap)
    store = get_vector_store(chunks, settings)
    retriever = get_retriever(store, settings)
    chain = build_rag_pipeline(settings)

    answers = []
    for question in questions[question_col].astype(str):
        result = answer_question(question, retriever, chain)
        answers.append(result["answer"].replace("\\n", " ").strip())

    output = pd.DataFrame({"question_id": questions["question_id"], "answer": answers})
    output.to_csv(output_csv, index=False)
    validate_submission(output_csv, expected_ids=questions["question_id"].tolist())
    return Path(output_csv)

def validate_submission(path: str, expected_ids=None):
    df = pd.read_csv(path)
    if list(df.columns) != ["question_id", "answer"]:
        raise ValueError("submission.csv must have exactly: question_id, answer")
    if len(df) != 20:
        raise ValueError(f"submission.csv must contain exactly 20 data rows; found {len(df)}.")
    if df.isna().any().any() or (df["answer"].astype(str).str.strip() == "").any():
        raise ValueError("Submission contains missing or empty values.")
    if df["question_id"].duplicated().any():
        raise ValueError("Submission contains duplicate question IDs.")
    if expected_ids is not None and df["question_id"].tolist() != list(expected_ids):
        raise ValueError("Submission question IDs/order do not match the supplied input.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", required=True, help="CSV exported from the competition starter notebook")
    parser.add_argument("--output", default="submission.csv")
    args = parser.parse_args()
    print(generate_submission(args.questions, args.output))
