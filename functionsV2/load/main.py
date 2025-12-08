import io
import os
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse

import pandas as pd
import requests


def fetch_remote_stream(url: str) -> io.BytesIO:
    """Download a remote file and return it as an in-memory stream."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SkillMatrixFetcher/1.0)",
    }
    token = os.getenv("GCS_ACCESS_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return io.BytesIO(response.content)


def read_tabular_data(file_path: str, sheet_name: str | int = 0) -> List[Dict[str, Any]]:
    """
    Read a CSV or Excel file (local path or HTTP(S) URL) and return its rows.

    Args:
        file_path: Absolute/relative path or HTTP(S) URL to the file.
        sheet_name: Sheet index or name when reading Excel workbooks.

    Returns:
        A list of dictionaries where each dict represents a row keyed by column name.
    """
    parsed = urlparse(file_path)
    is_remote = parsed.scheme in {"http", "https"}
    is_csv = file_path.lower().endswith(".csv")

    data_source: str | io.BytesIO
    if is_remote:
        data_source = fetch_remote_stream(file_path)
    else:
        tabular_path = Path(file_path)
        if not tabular_path.exists():
            raise FileNotFoundError(f"File not found: {tabular_path}")
        data_source = str(tabular_path)

    try:
        if is_csv:
            df = pd.read_csv(data_source)
        else:
            df = pd.read_excel(data_source, sheet_name=sheet_name)
    except ValueError as exc:
        raise ValueError(f"Unable to read '{file_path}': {exc}") from exc

    return df.to_dict(orient="records")


def main() -> None:
    target_file = "INFOLDER_Master_Skills.csv"
    sheet = 0  # Ignored for CSV files.

    rows = read_tabular_data(target_file, sheet_name=sheet)
    print(f"Read {len(rows)} rows from '{target_file}'.")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()

