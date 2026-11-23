# Dependency Security Audit

Requirement: `sec.no_critical_cves`. No dependency may have a CRITICAL or HIGH CVE
that already has a fixed version.

## Scope

- `backend/requirements.txt` (Python, pip)
- `frontend/package.json` (Node.js, npm)

## How to audit

```bash
# Backend
pip install pip-audit
pip-audit -r backend/requirements.txt

# Frontend
cd frontend && npm audit --audit-level=high

# Whole repository / container image
trivy fs --severity HIGH,CRITICAL --ignore-unfixed .
```

Run these before every deployment. If any HIGH/CRITICAL finding has a fixed
version, the build must not be deployed until the pin is updated.

## Remediated findings

| Package | Old version | New version | CVEs addressed |
|---------|-------------|-------------|----------------|
| Django  | 5.1.4       | 5.2.19      | CVE-2025-57833, CVE-2025-64459, PYSEC-2026-198/199/201/2090/2091/2092/3717/4035 (5.1 is end-of-life; no 5.1.x fix for later advisories) |
| djangorestframework | 3.15.2 | 3.18.3 | CVE-2026-114137, CVE-2026-114138, CVE-2026-114136, PYSEC-2026-3827/3828 |
| python-dotenv | 1.0.1 | 1.2.4 | PYSEC-2026-2270 |
| react-router-dom (→ @remix-run/router) | 6.28.0 (router 1.21.0) | 6.30.6 | CVE-2026-22029 (XSS via open redirects) |
| vite    | 5.4.11      | 6.4.6       | High advisory on vite <=6.4.3 (plus moderate esbuild/dev-server advisories); vite 5.x has no fixed release |

The other backend pins (`psycopg[binary]==3.2.3`,
`django-cors-headers==4.6.0`, `python-dotenv==1.0.1`, `gunicorn==23.0.0`) had no
known HIGH/CRITICAL CVE with a fix available when this was reviewed.
`gunicorn==23.0.0` already contains the fix for the HTTP request smuggling CVEs
(CVE-2024-1135, CVE-2024-6827).

## Accepted risk (no fix available)

| Package | CVE | Severity | Justification | Review date |
|---------|-----|----------|---------------|-------------|
| react-router / react-router-dom | GHSA-wrjc-x8rr-h8h6, GHSA-337j-9hxr-rhxg | Moderate | Fix requires react-router 7 (breaking change); the app uses only client-side routing, no SSR hydration. Moderate severity, outside the HIGH/CRITICAL gate. | 2027-02-20 |

Add a row here for any HIGH/CRITICAL CVE that has no fixed release yet. Give a
justification (for example, the vulnerable code path is not used) and a review
date no more than 90 days away.

## Audit log

| Date       | Tooling                       | Result |
|------------|-------------------------------|--------|
| 2026-11-20 | Manual review of pins against public advisories (GitHub Advisory DB / Django security releases) | Django moved to 5.1.15; no other HIGH/CRITICAL findings with fixes known |
| 2026-11-23 | pip-audit 2.x on backend/requirements.txt; npm audit on frontend | Backend: no known vulnerabilities after bumps. Frontend: 0 high, 2 moderate (react-router, see accepted risk) |

## Notes

Django 5.2 is the current LTS line and is now pinned. Django 5.1 is end-of-life, so
its pins must not be reverted. Plan the react-router 7 migration to clear the
remaining moderate advisories.
