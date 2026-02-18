import os
from fastapi import Header, HTTPException

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "").strip()
if not API_KEY:
    raise RuntimeError("API_KEY não configurada.")

def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida.")
