## 🌐 Domain and DNS structure for pinksync.io  
Cloudflare becomes the **authoritative DNS** for:

```
pinksync.io
*.pinksync.io
*.pinksync.vr4deaf.org (if you keep the org domain)
```

### Recommended DNS setup  
- `A` or `AAAA` → your origin (if using VM/container)  
- `CNAME` → your cloud provider (if using Azure, Fly.io, Railway, etc.)  
- `CNAME` flattening for apex domain  
- Wildcard subdomain support:  
  ```
  *.pinksync.io → proxied through Cloudflare
  ```

This allows you to dynamically create:

```
acme.pinksync.io
fibonrose.pinksync.io
node1.acme.pinksync.io
pinkflow.pinksync.io
```

without touching DNS again.

---

## 🚀 Protocol support: HTTP/1.1, HTTP/2, HTTP/3 (QUIC)  
Cloudflare automatically negotiates the best protocol with the client:

- **HTTP/3 (QUIC)** for browsers and mobile apps that support it  
- **HTTP/2** for most modern clients  
- **HTTP/1.1** fallback  
- **TCP proxying** if you enable Spectrum (paid)  
- **UDP proxying** for QUIC passthrough (Enterprise)  

For PinkSync, the best setup is:

### Recommended  
- Enable **HTTP/3**  
- Enable **HTTP/2**  
- Keep **HTTP/1.1** fallback  
- Do **not** use Spectrum unless you need raw TCP/UDP services  

PinkSync is an API → HTTP/2 + HTTP/3 is ideal.

---

## 🧭 Routing model for partners and nodes  
Cloudflare Workers or Cloudflare Load Balancer can route based on subdomain patterns.

### Pattern  
```
<partner>.pinksync.io
<node>.<partner>.pinksync.io
```

### Worker routing example  
```js
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const host = url.hostname;

    if (host.endsWith(".pinksync.io")) {
      const parts = host.split(".");
      const partner = parts[0];
      const node = parts.length === 3 ? null : parts[0];
      const service = parts.length === 3 ? parts[1] : null;

      // Route to your backend
      return fetch(env.PINKSYNC_ORIGIN + url.pathname, request);
    }
  }
}
```

This gives you dynamic partner routing without touching DNS.

---

## 🔁 Redirects and rewrites  
Cloudflare Rules let you define:

- partner onboarding redirects  
- vanity URLs  
- versioned API paths  
- workflow‑specific routing  

Examples:

### Redirect old API to new API  
```
/api/* → /v1/$1
```

### Redirect partner vanity domain  
```
acme.pinksync.io/docs → https://docs.pinksync.io/partners/acme
```

### Redirect node to partner root  
```
node1.acme.pinksync.io → acme.pinksync.io
```

---

## 🔐 Security and identity at the edge  
Cloudflare gives you:

- WAF  
- Bot protection  
- Rate limiting  
- mTLS (if needed)  
- API Shield (schema validation)  
- JWT validation at the edge  

For PinkSync, the most important are:

### 1. API Shield  
Upload your OpenAPI spec → Cloudflare validates requests before they hit your origin.

### 2. Rate limiting  
Per partner, per node, per IP.

### 3. mTLS (optional)  
If you want PinkFlow → PinkSync to be mutually authenticated.

---

## 🧩 Cloudflare + PinkSync architecture  
This is the recommended full setup:

```
Client
   │
   ▼
Cloudflare Edge
   │  (HTTP/3, HTTP/2, HTTP/1.1)
   │  WAF, API Shield, Rate Limits
   │  Subdomain Routing
   ▼
PinkSync API (FastAPI)
   │
   ▼
PinkFlow Orchestrator
   │
   ▼
Database (Neon/Supabase)
```

---

## 🧠 How this supports your partner_id / node_id model  
Cloudflare gives you:

### 1. Subdomain identity  
```
acme.pinksync.io → partner_id = acme
node1.acme.pinksync.io → node_id = node1
```

### 2. Edge‑level routing  
Workers can inject:

```
X-PinkSync-Partner: acme
X-PinkSync-Node: node1
```

### 3. Edge‑level rate limiting  
Per partner or per node.

### 4. Edge‑level auth  
Validate API keys or JWT before hitting your backend.

---

## 🧠 How this supports PinkFlow  
PinkFlow can:

- call PinkSync via Cloudflare  
- receive webhooks through Cloudflare  
- use mTLS or JWT for secure service‑to‑service calls  
- rely on Cloudflare for global routing  

---

## 🧩 Summary  
Cloudflare can handle **all of pinksync.io**, including:

- DNS  
- subdomains  
- partner routing  
- node routing  
- redirects  
- HTTP/2 + HTTP/3 (QUIC)  
- API Shield  
- WAF  
- rate limiting  
- Workers for logic  
- KV/Queues for async tasks  
- Durable Objects for partner state  

This gives PinkSync a global, low‑latency, secure edge layer that matches your partner architecture perfectly.

---

