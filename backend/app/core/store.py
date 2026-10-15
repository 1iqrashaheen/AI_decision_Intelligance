"""In-memory dataset store (temporary). Saud's PostgreSQL layer replaces this."""
import uuid
from typing import Dict

import pandas as pd

DATASETS: Dict[str, pd.DataFrame] = {}


def save_dataset(df: pd.DataFrame) -> str:
    dataset_id = uuid.uuid4().hex[:12]
    DATASETS[dataset_id] = df
    return dataset_id
