### 1. How PinkFlow calls PinkSync  
Developers want a clear contract:

- endpoint names  
- required headers  
- required tokens  
- payload shape  
- expected responses  
- error codes  
- retry behavior  
- webhook callbacks  

This is the “execution contract.”

### 2. How partners are identified  
They need to know:

- partner_id  
- node_id  
- identifier  
- subdomain rules  
- auth method (API key, OAuth2, bearer)  
- rate limits  
- scopes  

This is the “identity contract.”

### 3. How workflows are structured  
They want:

- step definitions  
- step input/output  
- how to chain steps  
- how to resume async steps  
- how to handle failures  
- how to register new workflows  

This is the “workflow contract.”

### 4. How to register a partner service  
They need:

- how to create a partner entry  
- how to attach webhook endpoints  
- how to define partner actions  
- how to test partner integration  
- how to rotate secrets  

This is the “partner contract.”

---

## What that “one shot” deliverable looks like
A real developer would expect a **single document** (or README) containing:

### 🧱 1. Identity Model (FIM‑style)
```
partner_id: UUIDv7
node_id: UUIDv7
identifier: "<partner>.pinksync.vr4deaf.org"
auth_method: "api_key" | "oauth2" | "bearer"
scopes: ["sign:read", "sign:write"]
status: "active"
```

### 🔌 2. API Contract (PinkFlow → PinkSync)
```
POST /v1/execute/{action}
Authorization: Bearer <PINKFLOW_TOKEN>
Content-Type: application/json

{
  "workflow_id": "UUID",
  "step_id": "UUID",
  "payload": { ... }
}
```

### 🔄 3. Webhook Contract (PinkSync → PinkFlow)
```
POST /webhooks/pinksync
svix-signature: <signature>

{
  "workflow_id": "UUID",
  "step_id": "UUID",
  "status": "completed",
  "output": { ... }
}
```

### 🧩 4. Workflow Step Template
```
async function step(context) {
  return pinksync.execute("sign_to_text", {
    video_url: context.input.video_url
  });
}
```

### 🏷 5. Partner Registration Template
```
POST /admin/partners
{
  "name": "Fibonrose",
  "identifier": "fibonrose.pinksync.vr4deaf.org",
  "auth_method": "oauth2",
  "webhook_url": "https://fibonrose.com/hooks/pinksync",
  "rate_limit_per_minute": 100
}
```

### 🧭 6. Subdomain Assignment Rules
```
<partner>.pinksync.vr4deaf.org
<node>.<partner>.pinksync.vr4deaf.org
```

### 🧪 7. Example End‑to‑End Flow
1. PinkFlow receives a trigger  
2. PinkFlow calls PinkSync `/execute/sign_to_text`  
3. PinkSync processes  
4. PinkSync sends webhook back  
5. PinkFlow resumes workflow  
6. Next step runs  

---

## Why developers want this “one shot”
Because it gives them:

- the **contract**  
- the **identity model**  
- the **workflow pattern**  
- the **integration pattern**  
- the **subdomain rules**  
- the **security model**  

All in one place, without digging through repos.

---

## What you should create next
A **single integration blueprint file** that lives at:

```
/docs/integration-blueprint.md
```

This becomes the “one shot” developers ask for.
