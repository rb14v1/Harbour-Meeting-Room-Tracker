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
| Django  | 5.1.4       | 5.1.15      | CVE-2025-57833 (SQL injection via FilteredRelation column aliases), CVE-2025-64459 (SQL injection via `_connector` kwarg in QuerySet/Q), plus the other security fixes released in 5.1.5–5.1.15 |

The other backend pins (`djangorestframework==3.15.2`, `psycopg[binary]==3.2.3`,
`django-cors-headers==4.6.0`, `python-dotenv==1.0.1`, `gunicorn==23.0.0`) had no
known HIGH/CRITICAL CVE with a fix available when this was reviewed.
`gunicorn==23.0.0` already contains the fix for the HTTP request smuggling CVEs
(CVE-2024-1135, CVE-2024-6827).

## Accepted risk (no fix available)

| Package | CVE | Severity | Justification | Review date |
|---------|-----|----------|---------------|-------------|
| _none_  | –   | –        | No HIGH/CRITICAL CVEs without a fix are currently known. | 2027-02-20 |

Add a row here for any HIGH/CRITICAL CVE that has no fixed release yet. Give a
justification (for example, the vulnerable code path is not used) and a review
date no more than 90 days away.

## Audit log

| Date       | Tooling                       | Result |
|------------|-------------------------------|--------|
| 2026-11-20 | Manual review of pins against public advisories (GitHub Advisory DB / Django security releases) | Django moved to 5.1.15; no other HIGH/CRITICAL findings with fixes known |

## Notes

Django 5.1 extended support ended in December 2025. Plan an upgrade to a
supported LTS (Django 5.2.x) so future security fixes are still received.
