PinkSync and DeafAuth need a **shared runtime shape**: middleware that enforces policy, utilities that load tenant rules from Cloudflare KV, a context object passed through every request, and a clean port layout so services don’t collide. The repo you have open is a starter with no infra yet, so this fills in the missing architecture in a way that matches your multi‑tenant, HIPAA‑aware, KV‑driven design.

---

## Middleware for HIPAA, DeafAuth, and Tenant Policy  
Middleware is where PinkSync enforces:

- tenant identity  
- DeafAuth token validation  
- HIPAA mode  
- PHI redaction  
- LLM/robots restrictions  
- audit logging  
- rate limiting hooks  

### FastAPI middleware structure  
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from .policy_loader import get_policy
from .deafauth import verify_deafauth_token

async def pinksync_middleware(request: Request, call_next):
    tenant_id = request.headers.get("X-Tenant-ID")
    auth_header = request.headers.get("Authorization")

    # Load tenant policy from Cloudflare KV
    policy = await get_policy(tenant_id)

    # Validate DeafAuth token
    token = verify_deafauth_token(auth_header, policy)

    # Enforce HIPAA mode
    if policy["hipaa_mode"]:
        request.state.hipaa = True
        request.state.store_phi = policy["store_phi"]
        request.state.audit_level = policy["audit_log"]
        request.state.allow_llm_context = policy["allow_llm_context"]
    else:
        request.state.hipaa = False

    # Attach user + tenant context
    request.state.user_id = token["sub"]
    request.state.tenant_id = tenant_id
    request.state.policy = policy

    response = await call_next(request)
    return response
```

This middleware becomes the **gatekeeper** for every PinkSync action.

---

## Utility Layer (KV loader, token tools, PHI redaction)  
Utilities are small, reusable modules that PinkSync and DeafAuth both rely on.

### 1. Cloudflare KV loader  
```python
import json
from cloudflare_kv import KVClient

kv = KVClient(namespace="pinksync")

async def get_policy(tenant_id: str):
    raw = await kv.get("PINKSYNC_POLICY")
    policies = json.loads(raw)

    if tenant_id in policies["tenants"]:
        return policies["tenants"][tenant_id]

    return policies["default"]
```

### 2. DeafAuth token verification  
```python
import jwt

def verify_deafauth_token(auth_header, policy):
    if not auth_header:
        raise Exception("Missing Authorization header")

    token = auth_header.replace("Bearer ", "")
    decoded = jwt.decode(token, "DEFAUTH_SECRET", algorithms=["HS256"])

    # Enforce tenant HIPAA rules
    if policy["hipaa_mode"] and decoded.get("hipaa_mode") != True:
        raise Exception("Token not HIPAA-compliant")

    return decoded
```

### 3. PHI redaction utility  
```python
def redact_phi(data: dict):
    safe = {}
    for k, v in data.items():
        if "name" in k or "dob" in k or "address" in k:
            safe[k] = "[REDACTED]"
        else:
            safe[k] = v
    return safe
```

---

## Request Context Object  
Every request gets a **context** object injected by middleware.

### Example  
```python
class PinkSyncContext:
    user_id: str
    tenant_id: str
    hipaa: bool
    store_phi: bool
    audit_level: str
    allow_llm_context: bool
    policy: dict
```

### How services use it  
```python
async def run_sign_to_text(payload, ctx):
    if ctx.hipaa and not ctx.store_phi:
        payload = redact_phi(payload)

    # Continue processing...
```

This keeps your service code clean and HIPAA‑safe.

---

## Library Structure (shared code for DeafAuth + PinkSync)  
A real developer would break it into:

```
pinksync/
  middleware/
    auth.py
    hipaa.py
    context.py
  utils/
    kv_loader.py
    redact.py
    tokens.py
  services/
    sign_to_text.py
    text_to_sign.py
    overlay.py
  protocols/
    deafauth.py
    pinksync.py
  routers/
    execute.py
    webhooks.py
```

This gives you a **protocol‑driven** architecture.

---

## Ports and Service Layout  
You asked:

> ports (3001 - deafauth, 3002 for pinksync or can use cloudfunnel?)

### Recommended local ports  
- **3001 → DeafAuth service**  
- **3002 → PinkSync execution engine**  
- **3003 → PinkFlow orchestrator** (optional)

### In production  
Cloudflare sits in front of everything:

```
pinksync.io → Cloudflare → PinkSync (3002 internal)
deafauth.pinksync.io → Cloudflare → DeafAuth (3001 internal)
pinkflow.pinksync.io → Cloudflare → PinkFlow (3003 internal)
```

You do **not** expose ports publicly.  
Cloudflare handles:

- TLS  
- HTTP/2  
- HTTP/3 (QUIC)  
- subdomain routing  
- WAF  
- API Shield  
- rate limiting  

Your services only need to listen on internal ports.

---

## Cloudflare “Cloudfunnel” (Workers + KV + Routing)  
Cloudflare becomes your **service mesh**:

- Routes partner subdomains  
- Injects tenant_id  
- Injects partner_id  
- Validates API keys  
- Loads policy from KV  
- Blocks PHI exposure  
- Enforces robots.txt  
- Sends traffic to the correct internal port  

### Example Worker routing  
```js
export default {
  async fetch(request, env) {
    const host = new URL(request.url).hostname;

    if (host.startsWith("deafauth.")) {
      return fetch(env.DEFAUTH_URL, request);
    }

    if (host.startsWith("pinkflow.")) {
      return fetch(env.PINKFLOW_URL, request);
    }

    return fetch(env.PINKSYNC_URL, request);
  }
}
```

This is your “cloud funnel.”



