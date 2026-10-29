import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from backend.app.core.auth import require_user
from backend.app.core.database import SessionLocal, SavedScenario
from backend.app.core.errors import APIError
from backend.app.core.store import owns_dataset
router=APIRouter(prefix='/saved',tags=['saved results'])
class SaveScenario(BaseModel):
    name: str = Field(min_length=1,max_length=120)
    dataset_id: str | None = None
    scenario: dict
@router.post('/scenarios')
def save_scenario(body: SaveScenario,user=Depends(require_user)):
    if body.dataset_id and not owns_dataset(body.dataset_id,user['id']):
        raise APIError(404,'dataset_not_found','Dataset not found or you do not have access to it.')
    with SessionLocal() as db:
        row=SavedScenario(owner_id=user['id'],name=body.name.strip(),dataset_id=body.dataset_id,scenario_json=json.dumps(body.scenario))
        db.add(row);db.commit();db.refresh(row)
        return {'id':row.id,'name':row.name,'dataset_id':row.dataset_id,'scenario':body.scenario,'created_at':row.created_at.isoformat() if row.created_at else None}
@router.get('/scenarios')
def list_scenarios(user=Depends(require_user)):
    with SessionLocal() as db:
        rows=db.scalars(select(SavedScenario).where(SavedScenario.owner_id==user['id']).order_by(SavedScenario.id.desc())).all()
        return [{'id':r.id,'name':r.name,'dataset_id':r.dataset_id,'scenario':json.loads(r.scenario_json),'created_at':r.created_at.isoformat() if r.created_at else None} for r in rows]
@router.get('/scenarios/{scenario_id}')
def get_scenario(scenario_id:int,user=Depends(require_user)):
    with SessionLocal() as db:
        row=db.get(SavedScenario,scenario_id)
        if not row or row.owner_id != user['id']: raise APIError(404,'scenario_not_found','Saved scenario not found.')
        return {'id':row.id,'name':row.name,'dataset_id':row.dataset_id,'scenario':json.loads(row.scenario_json),'created_at':row.created_at.isoformat() if row.created_at else None}
