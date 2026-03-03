## 🧩 DeafAuth Protocol (User Authentication Layer)
DeafAuth is the **user-facing** protocol. It defines how a user proves identity using:

- gesture recognition  
- sign‑video verification  
- passcode fallback  
- device binding  
- optional MFA  
- optional hardware key  
- optional biometric (if tenant allows)  

### Core handshake steps
1. **Client → PinkSync**:  
   Sends `tenant_id`, `user_id`, and `auth_method` (gesture, sign-video, etc.).

2. **PinkSync loads tenant policy**:  
   Determines allowed methods, HIPAA mode, MFA requirements.

3. **PinkSync challenges user**:  
   Example: “perform gesture X”, “sign phrase Y”, “provide passcode”.

4. **User responds**:  
   Video, gesture data, or passcode.

5. **PinkSync verifies**:  
   - ML model  
   - signature  
   - device binding  
   - MFA if required  

6. **PinkSync issues DeafAuth Token**:  
   A signed JWT-like token:

   ```
   {
     "sub": user_id,
     "tenant": tenant_id,
     "method": "gesture",
     "hipaa_mode": true,
     "iat": ...,
     "exp": ...
   }
   ```

This token is used for all subsequent PinkSync calls.

---

## 🧩 PinkSync Protocol (Service Execution Layer)
This is the **internal API contract** between PinkFlow, partners, and PinkSync.

### Required headers
```
Authorization: Bearer <DeafAuthToken>
X-Tenant-ID: <tenant_id>
X-Partner-ID: <partner_id> (optional)
```

### Required fields
```
workflow_id
step_id
payload
```

### Required behavior
- Reject if DeafAuth token is missing or expired  
- Reject if tenant policy forbids the action  
- Reject if HIPAA mode forbids storing raw media  
- Log every action for audit  

### Example request
```
POST /v1/execute/sign_to_text
Authorization: Bearer <DeafAuthToken>
X-Tenant-ID: clinic_x

{
  "workflow_id": "123",
  "step_id": "456",
  "payload": {
    "video_url": "...",
    "user_id": "abc"
  }
}
```

### Example response
```
{
  "status": "completed",
  "output": {
    "text": "Hello doctor",
    "confidence": 0.98
  }
}
```

---

## 🧩 Tenant Policy Protocol (The One File PinkSync Reads)
This is the **single source of truth** for all tenants.  
PinkSync loads it at startup and caches it.

### File name
```
deafauth_policies.yaml
```

### Structure
```yaml
default:
  hipaa_mode: false
  require_mfa: false
  allowed_methods:
    - gesture
    - sign_video
    - passcode
  store_phi: false
  audit_log: "minimal"

tenants:
  clinic_x:
    hipaa_mode: true
    require_mfa: true
    allowed_methods:
      - gesture
      - sign_video
    store_phi: false
    audit_log: "full"

  vr4deaf:
    hipaa_mode: true
    require_mfa: false
    allowed_methods:
      - gesture
      - sign_video
      - passcode
    store_phi: true
    audit_log: "full"
```

### Why this works
- **Individual**: each user gets their own DeafAuth token  
- **Multi‑tenant**: each tenant has its own block  
- **Agnostic**: PinkSync doesn’t care who the tenant is  
- **HIPAA**: tenants can enforce strict PHI rules  

### What PinkSync reads from this file
- allowed auth methods  
- whether raw video can be stored  
- whether MFA is required  
- whether PHI can be logged  
- whether audit logs must be full or minimal  

This file is the **policy brain** of the entire system.

---

## 🧩 How all three protocols work together
### Example: A HIPAA clinic user signs in
1. User signs a gesture  
2. PinkSync checks `clinic_x` policy  
3. HIPAA mode = true → no raw video stored  
4. MFA required → PinkSync asks for passcode  
5. User passes  
6. PinkSync issues DeafAuth token  
7. PinkFlow uses that token to run workflows  
8. PinkSync enforces HIPAA rules on every step  

Everything is consistent because **all rules come from one file**.

---

## 🧠 Closing thought  
The missing piece now is deciding **where** to store `deafauth_policies.yaml`:

- in the repo  
- in Cloudflare KV  
- in Google Secret Manager  
- in Supabase storage  
- in Neon as a JSONB row  

Each option changes how dynamic your policies can be.
