# Backend (FastAPI) – Muhammad Arham

## Run
```
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```
Docs (try every endpoint): http://localhost:8001/docs

## Test
`python -m pytest -q`

## Endpoints (all under /api)
| Method | Path | Owner of real logic | Status |
|---|---|---|---|
| GET | /health | me | real |
| POST | /upload (multipart `file`) | me + Abdul (cleaning) | real parsing/quality, no cleaning yet |
| GET | /analysis/{dataset_id} | Ahsan | mock |
| POST | /forecast | Fazeela | mock |
| POST | /simulate | Arayash | placeholder (README formulas) |
| POST | /simulate/compare | Arayash | best/expected/worst |
| POST | /chat | Iqra | mock |
| POST | /export?format=pdf\|csv | me | real, sample data if no body |

## Conventions
- Percent changes are fractions: 0.10 = +10%.
- Errors always: `{"error": {"code": "...", "message": "...", "details": [...]}}`
- Teammates replace the function marked `MOCK`/`PLACEHOLDER`; schemas in `app/schemas/common.py` stay fixed unless the group agrees.
