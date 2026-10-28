"""Keep uploads in memory until Saud's database is connected."""
import uuid
from typing import Any, Dict, Optional

import pandas as pd

DATASETS: Dict[str, pd.DataFrame] = {}
DATASET_METADATA: Dict[str, Dict[str, Any]] = {}


def save_dataset(df: pd.DataFrame, meta: Optional[Dict[str, Any]] = None) -> str:
    dataset_id = uuid.uuid4().hex[:12]
    DATASETS[dataset_id] = df
    if meta:
        DATASET_METADATA[dataset_id] = meta
    return dataset_id


def get_dataset(dataset_id: str) -> Optional[pd.DataFrame]:
    return DATASETS.get(dataset_id)


def get_metadata(dataset_id: str) -> Dict[str, Any]:
    return DATASET_METADATA.get(dataset_id, {})
