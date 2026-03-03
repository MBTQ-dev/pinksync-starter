# PinkSync Integration Blueprint  
*A unified contract for PinkFlow, partner services, and external developers*  
*(Based on the PinkSync gateway, database schema, and infrastructure in this repository.)*   [github.com](https://github.com/MBTQ-dev/pinksync-starter/commit/c0a3b247dac23ae3bc045ce1750cdf27171046cc)

---

## 1. Identity Model  
PinkSync uses a federated‑identity‑style model for partners and nodes. This aligns with the `partners`, `api_keys`, `webhook_endpoints`, and `rate_limits` tables in the schema.

### Partner Identity
```
partner_id: UUIDv7
identifier: "<partner>.pinksync.vr4deaf.org"
type: "vendor" | "provider" | "platform"
status: "pending" | "active" | "suspended" | "inactive"
auth_method: "api_key" | "oauth2" | "bearer" | "basic"
rate_limit_per_minute: number
created_at: timestamp
updated_at: timestamp
```

### Node Identity (optional)
```
node_id: UUIDv7
partner_id: UUIDv7
identifier: "<node>.<partner>.pinksync.vr4deaf.org"
role: "ingest" | "delivery" | "processing"
status: "active" | "inactive"
```

### Subdomain Rules
Partners and nodes receive automatic subdomains:
```
https://<partner>.pinksync.vr4deaf.org
https://<node>.<partner>.pinksync.vr4deaf.org
```

These map cleanly to the gateway and webhook handler deployed via Azure Container Apps.   [github.com](https://github.com/MBTQ-dev/pinksync-starter/commit/c0a3b247dac23ae3bc045ce1750cdf27171046cc)

---

## 2. Authentication  
PinkSync supports the following authentication methods, matching the gateway code:

- **API Key** (bcrypt‑hashed in `api_keys`)  
- **OAuth2 Authorization Code Flow** (via simple‑oauth2)  
- **Bearer Tokens**  
- **Basic Auth**  

### API Key Header
```
Authorization: Bearer <api_key>
```

### OAuth2 Redirect
```
GET /oauth/authorize/:partnerId
```

### OAuth2 Callback
```
GET /oauth/callback
```

Tokens are encrypted and stored in the `partners.credentials` column.   [github.com](https://github.com/MBTQ-dev/pinksync-starter/commit/c0a3b247dac23ae3bc045ce1750cdf27171046cc)

---

## 3. PinkFlow → PinkSync Execution Contract  
PinkFlow orchestrates workflows. PinkSync executes actions.

### Request
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

### Response
```
{
  "status": "completed",
  "output": { ... },
  "duration_ms": 123
}
```

### Supported Actions
- `sign_to_text`
- `text_to_sign`
- `asl_overlay`
- `caption_video`
- `gesture_auth`
- `partner_action`
- `text_simplify`
- `dialect_transform`

Actions map to service modules inside PinkSync.

---

## 4. PinkSync → PinkFlow Webhook Contract  
PinkSync sends asynchronous results back to PinkFlow using Svix‑verified webhooks.

### Endpoint
```
POST /webhooks/pinksync
svix-id: <id>
svix-timestamp: <timestamp>
svix-signature: <signature>
```

### Payload
```
{
  "workflow_id": "UUID",
  "step_id": "UUID",
  "status": "completed" | "failed",
  "output": { ... },
  "error": null | { message, code }
}
```

Webhook verification uses the Svix secret stored in Key Vault.   [github.com](https://github.com/MBTQ-dev/pinksync-starter/commit/c0a3b247dac23ae3bc045ce1750cdf27171046cc)

---

## 5. Workflow Step Template (PinkFlow)

```ts
// pinkflow/workflows/steps/signToText.ts
import { pinksync } from "../clients/pinksync";

export async function signToTextStep(context) {
  const result = await pinksync.execute("sign_to_text", {
    video_url: context.input.video_url,
    user_id: context.user.id
  });

  return {
    text: result.text,
    confidence: result.confidence
  };
}
```

PinkFlow always calls PinkSync; PinkSync never calls PinkFlow except via webhook.

---

## 6. PinkSync Client Template (used by PinkFlow)

```ts
// pinkflow/clients/pinksync.ts
import axios from "axios";

export const pinksync = {
  async execute(action, payload) {
    const response = await axios.post(
      `${process.env.PINKSYNC_URL}/v1/execute/${action}`,
      payload,
      {
        headers: {
          Authorization: `Bearer ${process.env.PINKFLOW_TOKEN}`
        }
      }
    );

    return response.data;
  }
};
```

---

## 7. Partner Registration Contract  
Matches the onboarding flow in your gateway tests.   [github.com](https://github.com/MBTQ-dev/pinksync-starter/commit/c0a3b247dac23ae3bc045ce1750cdf27171046cc)

### Create Partner
```
POST /api/partners/connect
{
  "name": "Acme Corp",
  "type": "vendor",
  "api_endpoint": "https://api.acmecorp.com/v1",
  "auth_method": "api_key"
}
```

### Response
```
{
  "partner_id": "UUID",
  "api_key": "pk_live_abcdef123456",
  "status": "pending"
}
```

### Register Webhook Endpoint
```
POST /api/partners/{partner_id}/webhooks
{
  "url": "https://acme.com/webhooks/pinksync",
  "events": ["order.created", "inventory.updated"]
}
```

Webhook secrets are stored in `webhook_endpoints.webhook_secret`.

---

## 8. Rate Limiting  
The gateway uses Redis‑based rate limiting with per‑partner windows.   [github.com](https://github.com/MBTQ-dev/pinksync-starter/commit/c0a3b247dac23ae3bc045ce1750cdf27171046cc)

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1712345678
```

---

## 9. Logging and Monitoring  
PinkSync logs events to:

- `integration_logs` table  
- Application Insights (custom metrics)  
- Grafana metrics endpoint  

Examples include:

- `connection.created`  
- `api.request`  
- `webhook.sent`  

These match the monitoring code in gateway.   [github.com](https://github.com/MBTQ-dev/pinksync-starter/commit/c0a3b247dac23ae3bc045ce1750cdf27171046cc)

---

## 10. End‑to‑End Example  
A complete flow from PinkFlow → PinkSync → PinkFlow:

1. PinkFlow receives a workflow trigger.  
2. PinkFlow calls PinkSync `/v1/execute/sign_to_text`.  
3. PinkSync processes the video.  
4. PinkSync sends webhook back to PinkFlow.  
5. PinkFlow resumes workflow and runs next step.  
6. Final output returned to the client or partner.

This pattern is consistent with your webhook handler and gateway architecture.   [github.com](https://github.com/MBTQ-dev/pinksync-starter/commit/c0a3b247dac23ae3bc045ce1750cdf27171046cc)

---

