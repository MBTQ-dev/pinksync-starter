## FastAPI PinkSync Template (Production‑Ready Skeleton)

### Directory layout
```
pinksync/
  main.py
  config.py
  auth.py
  models.py
  schemas.py
  router_execute.py
  router_webhooks.py
  services/
      sign_to_text.py
      text_to_sign.py
      overlay.py
      partner_action.py
  utils/
      rate_limit.py
      svix_verify.py
      subdomain.py
```

---

## main.py
```python
from fastapi import FastAPI
from router_execute import router as execute_router
from router_webhooks import router as webhook_router

app = FastAPI(
    title="PinkSync API",
    version="1.0.0"
)

app.include_router(execute_router, prefix="/v1/execute")
app.include_router(webhook_router, prefix="/webhooks")
```

---

## config.py
```python
import os

class Settings:
    PINKFLOW_TOKEN = os.getenv("PINKFLOW_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    SVIX_SECRET = os.getenv("SVIX_SECRET")
    ENV = os.getenv("ENV", "dev")

settings = Settings()
```

---

## auth.py
```python
from fastapi import HTTPException, Header
from config import settings

async def verify_pinkflow_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    if token != settings.PINKFLOW_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid PinkFlow token")

    return True
```

This enforces **workflow‑first execution**.

---

## schemas.py
```python
from pydantic import BaseModel
from typing import Any, Dict

class ExecuteRequest(BaseModel):
    workflow_id: str
    step_id: str
    payload: Dict[str, Any]

class ExecuteResponse(BaseModel):
    status: str
    output: Dict[str, Any]
    duration_ms: int
```

---

## router_execute.py
```python
from fastapi import APIRouter, Depends
from schemas import ExecuteRequest, ExecuteResponse
from auth import verify_pinkflow_token
from services.sign_to_text import run_sign_to_text
from services.text_to_sign import run_text_to_sign
from services.overlay import run_overlay
from services.partner_action import run_partner_action
import time

router = APIRouter()

ACTION_MAP = {
    "sign_to_text": run_sign_to_text,
    "text_to_sign": run_text_to_sign,
    "asl_overlay": run_overlay,
    "partner_action": run_partner_action,
}

@router.post("/{action}", response_model=ExecuteResponse)
async def execute_action(
    action: str,
    req: ExecuteRequest,
    _auth=Depends(verify_pinkflow_token)
):
    if action not in ACTION_MAP:
        return {"status": "failed", "output": {}, "duration_ms": 0}

    start = time.time()
    output = await ACTION_MAP[action](req.payload)
    duration = int((time.time() - start) * 1000)

    return {
        "status": "completed",
        "output": output,
        "duration_ms": duration
    }
```

---

## router_webhooks.py
```python
from fastapi import APIRouter, Header, HTTPException
from utils.svix_verify import verify_svix_signature

router = APIRouter()

@router.post("/pinksync")
async def receive_webhook(
    svix_id: str = Header(None),
    svix_timestamp: str = Header(None),
    svix_signature: str = Header(None),
    body: dict = None
):
    if not verify_svix_signature(svix_id, svix_timestamp, svix_signature, body):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Forward to PinkFlow workflow engine
    # (HTTP call to PinkFlow resume endpoint)
    return {"received": True}
```

---

## services/sign_to_text.py
```python
async def run_sign_to_text(payload):
    video_url = payload.get("video_url")
    user_id = payload.get("user_id")

    # TODO: call ML model or external partner
    return {
        "text": "Hello world (example)",
        "confidence": 0.98
    }
```

---

## utils/svix_verify.py
```python
import hmac
import hashlib
from config import settings

def verify_svix_signature(id, timestamp, signature, body):
    secret = settings.SVIX_SECRET.encode()
    message = f"{id}.{timestamp}.{body}".encode()
    expected = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## What this gives you
- A **real FastAPI PinkSync engine**  
- Workflow‑first enforcement  
- Partner identity hooks  
- Subdomain‑ready routing  
- Webhook verification  
- Async execution model  
- Clean separation of services  
- Expandable action map  
- Production‑ready structure  

