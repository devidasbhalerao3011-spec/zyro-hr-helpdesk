import os
import pandas as pd
from rag_pipeline import build_rag

TEST_FILE = "test.csv"
OUTPUT_FILE = "submission.csv"

def main():
    if not os.path.exists(TEST_FILE):
        raise FileNotFoundError(f"{TEST_FILE} not found in the project root.")
    df = pd.read_csv(TEST_FILE)
    if "question_id" not in df.columns:
        raise ValueError("test.csv must contain a question_id column.")
    question_col = next((c for c in ["question", "query", "prompt"] if c in df.columns), None)
    if question_col is None:
        raise ValueError("Could not find a question column. Expected question, query, or prompt.")
    rag = build_rag()
    answers = []
    for _, row in df.iterrows():
        answer, _ = rag.ask(str(row[question_col]))
        answers.append(answer.replace("\n", " ").strip())
    pd.DataFrame({"question_id": df["question_id"], "answer": answers}).to_csv(OUTPUT_FILE, index=False)
    print(f"Created {OUTPUT_FILE} with {len(answers)} answers.")

if __name__ == "__main__":
    main()
