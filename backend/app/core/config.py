import os

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
ALLOWED_EXT = {".csv", ".xlsx", ".xls"}
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:5500,http://localhost:3000",
    ).split(",")
]
