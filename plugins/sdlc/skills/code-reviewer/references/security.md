# security.md — Code Reviewer: Security Checklist

## When to load

Always loaded by the code-reviewer skill, regardless of stack or diff size. This file is non-optional. Do not skip or condition on stack — every review starts here.

---

## OWASP Top 10 (current edition) — review checklist

### A01 — Broken Access Control

What to look for in the diff: new endpoints or routes without authentication decorators (`@login_required`, `Depends(get_current_user)`, `requireAuth` middleware); object retrieval using user-supplied IDs without ownership check (IDOR pattern: `get_object_or_404(Model, pk=request.GET['id'])` without `.filter(owner=request.user)`); role/permission checks missing on sensitive operations; changes to `is_staff` / `is_superuser` / admin routes.

Common code smell: `queryset.filter(pk=pk)` where `pk` comes directly from request params with no user-scoping.

Fix direction: add ownership filter; add `@permission_required` / `Depends`; write a test that changes the ID to another user's and asserts 403.

### A02 — Cryptographic Failures

What to look for: MD5 or SHA1 used for passwords (`hashlib.md5`, `hashlib.sha1`); plaintext storage or transmission of sensitive data; hardcoded encryption keys or IVs in source; weak random (`random.random()` instead of `secrets`); HTTP URLs for sensitive endpoints; session tokens with insufficient entropy.

Common code smell: `import hashlib; hashlib.md5(password.encode()).hexdigest()`.

Fix direction: use `bcrypt` / `argon2` for passwords; use `secrets` module for tokens; enforce HTTPS at the config level.

### A03 — Injection

What to look for: raw SQL with f-strings or string concatenation (`cursor.execute(f"SELECT ... WHERE id={user_id}")`); Django `extra()` or `raw()` with user input; template injection via `Template(user_input).render()`; shell injection via `subprocess.run(f"cmd {user_input}", shell=True)`; LDAP / XPath queries built from user strings.

Common code smell: any f-string or `%`/`.format()` inside a SQL string or shell command.

Fix direction: use parameterized queries; use `subprocess.run([...])` with list (no `shell=True`); use ORM methods that escape automatically.

### A04 — Insecure Design

What to look for: business logic that can be bypassed by replaying a request out of order; missing rate limiting on auth endpoints; password reset flows without expiry or single-use tokens; workflows that reveal whether a user account exists via different error messages (user enumeration).

Common code smell: password reset link without expiry timestamp, or same reset token reusable multiple times.

Fix direction: token expiry (15 min max); single-use tokens; uniform error messages for login failures.

### A05 — Security Misconfiguration

What to look for: `DEBUG = True` in any non-local config file; `ALLOWED_HOSTS = ['*']`; `SECRET_KEY` present in version-controlled files; permissive CORS (`Access-Control-Allow-Origin: *` with credentials); default credentials in fixtures; disabled security middleware (CSRF, `SecurityMiddleware`); stack traces exposed to the client.

Common code smell: `SECRET_KEY = "dev-secret-key-change-in-prod"` in `settings.py` committed to repo.

Fix direction: move secrets to environment variables; use `django-environ` or `python-decouple`; assert `DEBUG = False` in prod configuration tests.

### A06 — Vulnerable and Outdated Components

What to look for: dependency changes in `requirements.txt`, `package.json`, `pyproject.toml`; packages pinned to old versions with known CVEs; unpinned `>=` dependencies that could resolve to a vulnerable version at install time; direct imports of unmaintained packages.

Common code smell: `Pillow==9.0.0` (known CVE) or `requests>=2.0` (could resolve old).

Fix direction: run `pip-audit` / `npm audit` as part of CI; pin to specific versions; check release notes for security patches.

### A07 — Identification and Authentication Failures

What to look for: JWT `alg: none` accepted; JWT secret present in code; no `exp` claim; session not invalidated on logout; no brute-force protection; auth bypass via type coercion. Common code smell: `jwt.decode(token, options={"verify_signature": False})`. Fix: enforce `alg` allowlist; set `exp`; invalidate sessions on logout.

### A08 — Software and Data Integrity Failures

What to look for: `pickle.loads(request.body)`, `yaml.load(data)` without `SafeLoader`, unsigned webhook payloads, `latest` tag in CI images, unpinned dependencies. Fix: `yaml.safe_load`; never deserialize untrusted binary; verify HMAC on webhooks; pin with hashes.

### A09 — Security Logging and Monitoring Failures

What to look for: auth failures not logged; successful privileged actions not logged; log messages that contain full stack traces with sensitive data (passwords, tokens in query strings); no audit trail for admin operations; exceptions caught and silently discarded without any log.

Common code smell: `except Exception: pass` — failure invisible to monitoring.

Fix direction: log auth events at INFO/WARNING; log admin mutations; scrub sensitive fields from log output; never silent-catch without at minimum `logger.exception(...)`.

### A10 — Server-Side Request Forgery (SSRF)

What to look for: user-supplied URLs passed to `requests.get()`, `httpx.get()`, `urllib.request.urlopen()`; webhooks or integrations where the target URL comes from user input; image/file URL fetching without domain allowlist; internal network endpoints accessible via user-controlled URL (`http://169.254.169.254/` metadata service).

Common code smell: `url = request.POST.get('webhook_url'); requests.post(url, ...)` without validation.

Fix direction: allowlist of permitted domains; block RFC-1918 / link-local ranges; use a DNS rebinding-resistant HTTP client.

---

## Secrets and credentials in code

Patterns to grep for in the diff — any match is a security item regardless of context ("it's just a test fixture" is not an exemption):

```
password\s*=\s*["'][^"']{3,}
api_key\s*=\s*["']
Bearer\s+[A-Za-z0-9\-_\.]{20,}
AKIA[0-9A-Z]{16}
-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY
token\s*=\s*["'][A-Za-z0-9\-_\.]{20,}
client_secret\s*=\s*["']
AWS_SECRET_ACCESS_KEY
DATABASE_URL\s*=\s*["'].*@
```

Severity: high. Always flag. Even if the value looks like a placeholder (`"changeme"`, `"xxx"`) — placeholder secrets committed to a repo become real secrets via git history.

Fix direction: move to environment variable; add the pattern to `.gitignore` / `.env.example`; rotate the credential immediately if it was real.

---

## Authentication and authorization

### Password hashing

Acceptable: `bcrypt` (via `passlib` or `django.contrib.auth`), `argon2-cffi`, PBKDF2 (Django default is acceptable; iterations should be current). Not acceptable: MD5, SHA1, SHA256 without salt, `hashlib` directly on passwords.

### Session handling

Check: session invalidated on logout (`request.session.flush()`); session ID regenerated after privilege escalation; session timeout configured; `SESSION_COOKIE_SECURE = True` and `SESSION_COOKIE_HTTPONLY = True` in Django.

### JWT pitfalls

- `alg: none` — algorithm confusion attack; always enforce an explicit allowlist.
- Secret in source code — treat the same as any hardcoded credential.
- Missing `exp` claim — token never expires; replay attack window is infinite.
- Missing `aud` claim — token accepted by unintended services.

### IDOR (Insecure Direct Object Reference)

Pattern: user-supplied ID → server retrieves object without ownership check. Test: change the ID to another user's resource — if it returns 200, it is IDOR.

### Missing decorators (Python)

- Django: `@login_required`, `@permission_required`, `LoginRequiredMixin`.
- FastAPI: `Depends(get_current_user)` in route signature.

A new route without one of these is a review item; the implementer determines if it is intentionally public.

---

## Injection vectors (detail)

| Vector | Grep pattern | Severity | Fix direction |
|---|---|---|---|
| SQL (raw) | `cursor.execute(f"` or `cursor.execute("...".format(` | Critical | Parameterized queries |
| SQL (Django extra/raw) | `.extra(where=` or `.raw(f"` | High | Use ORM; audit if unavoidable |
| Template | `Template(user_input)` or `render_template_string(user_input)` | High | Never render user input as template |
| Shell | `subprocess.*shell=True` with string concat | Critical | Pass list; never `shell=True` with user data |
| Path traversal | `open(user_input)` or `os.path.join(..., user_input)` without validation | High | Allowlist paths; resolve and verify prefix |
| LDAP | String-built LDAP filters | High | Use LDAP-safe escaping library |
| Eval | `eval(user_input)` or `exec(user_input)` | Critical | Never eval user input |

---

## CSRF / CORS / CSP

### CSRF

- Is Django's `CsrfViewMiddleware` present in `MIDDLEWARE`? If a view has `@csrf_exempt` — is the exemption justified and documented?
- For APIs using token auth (JWT/session), is `SameSite=Strict` or `SameSite=Lax` on the session cookie, or is a CSRF token still required?

### CORS

- `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` — forbidden by spec but misconfigured servers emit both. Flag if present.
- Allowed origins should be an explicit allowlist, not a wildcard for credentialed requests.
- Changes to `CORS_ALLOWED_ORIGINS` or `CORS_ORIGIN_WHITELIST` in diff — review the list for unintended entries.

### CSP

- If the app sets a `Content-Security-Policy` header, check for `script-src 'unsafe-inline'` or `script-src 'unsafe-eval'` — these defeat XSS protections.
- `default-src *` is effectively no CSP.
- New inline `<script>` tags without a nonce violate strict CSP.

---

## Output integration

Every review report produced by `sdlc:code-reviewer` must contain a `## Security` section. Content rules:

- If issues found: list each as `file:path:line — <OWASP category> — <evidence> — <fix direction>`.
- If no issues found: write exactly "no security issues found in scope" — do not omit the section.
- Severity labels: **critical** (exploitable now, no prerequisites), **high** (exploitable with low effort), **medium** (exploitable with prerequisites), **low** (defense-in-depth, not directly exploitable).

---

## When in doubt — escalate

If a finding is plausibly exploitable but the reviewer is uncertain about severity or reproduction:

- Flag as `security/maybe` with a reproduction request: "unconfirmed — implementer to verify by running `<specific test or curl command>`."
- Do not silently skip uncertain findings. False positives are cheaper than missed exploits.
- When unsure whether a pattern is intentional (e.g. `@csrf_exempt` on an API endpoint) — flag it and ask for justification. The justification then becomes part of the review artifact.
