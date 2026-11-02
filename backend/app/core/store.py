"""Persistent dataframe storage with a compatibility cache for existing analysis modules."""
import json, uuid
from typing import Any, Dict, Optional
import pandas as pd
from backend.app.core.database import SessionLocal, Dataset, init_db
DATASETS: Dict[str,pd.DataFrame]={}; DATASET_METADATA: Dict[str,Dict[str,Any]]={}; DATASET_OWNERS: Dict[str,int|None]={}

def _load_row(row):
    try:
        df=pd.read_json(row.dataframe_json,orient='split')
        meta=json.loads(row.metadata_json or '{}')
        DATASETS[row.id]=df; DATASET_METADATA[row.id]=meta; DATASET_OWNERS[row.id]=row.owner_id
        return df
    except Exception: return None

def save_dataset(df: pd.DataFrame, meta: Optional[Dict[str,Any]]=None, owner_id: int|None=None) -> str:
    init_db(); dataset_id=uuid.uuid4().hex[:12]; meta=meta or {}
    payload=df.to_json(orient='split',date_format='iso',date_unit='ms')
    with SessionLocal() as db:
        db.add(Dataset(id=dataset_id,owner_id=owner_id,filename=str(meta.get('filename','upload'))[:255],dataframe_json=payload,metadata_json=json.dumps(meta,default=str)))
        db.commit()
    DATASETS[dataset_id]=df;DATASET_METADATA[dataset_id]=meta;DATASET_OWNERS[dataset_id]=owner_id
    return dataset_id

def get_dataset(dataset_id: str, owner_id: int|None=None, enforce_owner: bool=False):
    if dataset_id in DATASETS:
        actual=DATASET_OWNERS.get(dataset_id)
        if enforce_owner and actual != owner_id: return None
        return DATASETS[dataset_id]
    init_db()
    with SessionLocal() as db:
        row=db.get(Dataset,dataset_id)
        if not row or (enforce_owner and row.owner_id != owner_id): return None
        return _load_row(row)

def get_metadata(dataset_id: str) -> Dict[str,Any]:
    if dataset_id in DATASET_METADATA: return DATASET_METADATA[dataset_id]
    init_db()
    with SessionLocal() as db:
        row=db.get(Dataset,dataset_id)
        if not row:return {}
        _load_row(row);return DATASET_METADATA.get(dataset_id,{})

def owns_dataset(dataset_id: str, owner_id: int|None) -> bool:
    if dataset_id in DATASET_OWNERS: return DATASET_OWNERS[dataset_id] == owner_id
    init_db()
    with SessionLocal() as db:
        row=db.get(Dataset,dataset_id)
        if not row:return False
        _load_row(row);return row.owner_id == owner_id
