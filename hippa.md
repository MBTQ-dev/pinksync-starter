## 🧩 HIPAA requirements PinkSync must enforce
HIPAA affects how PinkSync handles:

- **PHI storage** (raw video, transcripts, gesture data)  
- **PHI transmission** (encryption, tokenization)  
- **PHI exposure** (LLM training, logs, analytics)  
- **Audit logging** (full vs minimal)  
- **Access control** (per‑tenant, per‑user)  
- **Data retention** (delete windows, redaction rules)  

PinkSync must enforce these rules *per tenant*, not globally.

---

## 🧩 The “one file” PinkSync reads from Cloudflare KV
This file becomes the **DeafAuth + HIPAA + LLM Exposure Policy**.

### KV key
```
PINKSYNC_POLICY
```

### KV value (JSON)
```json
{
  "default": {
    "hipaa_mode": false,
    "store_phi": false,
    "allow_llm_training": false,
    "allow_llm_context": true,
    "robots": {
      "allow_crawl": false,
      "allow_index": false
    },
    "allowed_auth_methods": ["gesture", "sign_video", "passcode"],
    "audit_log": "minimal"
  },
  "tenants": {
    "clinic_x": {
      "hipaa_mode": true,
      "store_phi": false,
      "allow_llm_training": false,
      "allow_llm_context": false,
      "robots": {
        "allow_crawl": false,
        "allow_index": false
      },
      "allowed_auth_methods": ["gesture", "sign_video"],
      "audit_log": "full"
    },
    "vr4deaf": {
      "hipaa_mode": true,
      "store_phi": true,
      "allow_llm_training": false,
      "allow_llm_context": true,
      "robots": {
        "allow_crawl": false,
        "allow_index": false
      },
      "allowed_auth_methods": ["gesture", "sign_video", "passcode"],
      "audit_log": "full"
    }
  }
}
```

This single object controls:

- **HIPAA mode**  
- **PHI storage rules**  
- **LLM exposure rules**  
- **robots.txt behavior**  
- **allowed DeafAuth methods**  
- **audit logging level**  

PinkSync loads this once and applies it to every request.

---

## 🧩 How PinkSync enforces HIPAA + LLM + robots rules
### 1. HIPAA mode
If `hipaa_mode = true`:

- No raw video stored  
- No PHI in logs  
- No PHI in LLM context  
- MFA required  
- Audit logs must be full  
- All data encrypted at rest and in transit  

### 2. PHI storage
If `store_phi = false`:

- PinkSync must redact or delete raw media immediately  
- Only derived metadata allowed  

### 3. LLM exposure
Two separate controls:

- `allow_llm_training` → whether PHI can be used to train internal models  
- `allow_llm_context` → whether PHI can be passed to an LLM at runtime  

HIPAA tenants almost always set both to **false**.

### 4. robots.txt‑style behavior
PinkSync can generate a dynamic robots.txt per tenant:

```
User-agent: *
Disallow: /
```

Or allow crawling for non‑HIPAA tenants:

```
User-agent: *
Allow: /
```

This is controlled by:

```
robots.allow_crawl
robots.allow_index
```

### 5. DeafAuth method enforcement
PinkSync checks:

```
allowed_auth_methods
```

If a tenant forbids passcode, PinkSync rejects it.

---

## 🧩 How this works with multi‑tenant and agnostic design
PinkSync does not need to know anything about the tenant’s business.  
It only needs:

```
tenant_id
```

Then it loads:

```
policy = KV["PINKSYNC_POLICY"]
tenant_policy = policy.tenants[tenant_id] or policy.default
```

Everything else is automatic.

---

## 🧩 How this protects LLMs from PHI leakage
PinkSync must check:

```
allow_llm_context
```

before sending any user data to:

- OpenAI  
- Anthropic  
- Gemini  
- Local LLMs  
- Vector databases  

If `false`, PinkSync must:

- redact PHI  
- block the request  
- or use a non‑LLM fallback  

This is required for HIPAA compliance.

---

## 🧩 How this protects robots/crawlers
PinkSync can serve a dynamic robots.txt:

### HIPAA tenant
```
User-agent: *
Disallow: /
```

### Non‑HIPAA tenant
```
User-agent: *
Allow: /
```

This prevents accidental PHI exposure to search engines.

---

## 🧠 Summary
Cloudflare KV becomes the **policy brain** for:

- HIPAA  
- DeafAuth  
- LLM exposure  
- robots.txt  
- PHI storage  
- audit logging  
- allowed auth methods  
- tenant overrides  

PinkSync becomes the **policy enforcer**, not the policy owner.

---

