import pandas as pd
import pytest
from src.submission import validate_submission

def test_valid_twenty_row_submission(tmp_path):
    path = tmp_path / "submission.csv"
    pd.DataFrame({
        "question_id": list(range(20)),
        "answer": [f"Answer {i}" for i in range(20)],
    }).to_csv(path, index=False)
    assert validate_submission(path, expected_ids=list(range(20)))

def test_rejects_wrong_row_count(tmp_path):
    path = tmp_path / "submission.csv"
    pd.DataFrame({"question_id": [1], "answer": ["x"]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        validate_submission(path)
