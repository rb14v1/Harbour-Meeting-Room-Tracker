# Accepted dependency risks

Policy (`sec.no_critical_cves`): no dependency may ship with a CRITICAL or HIGH
CVE that has a fixed version available. CVEs with **no fix available** may be
accepted temporarily and must be listed below with a justification and a
review date.

## How dependencies are kept patched

- Python (`backend/requirements.txt`), npm (`frontend/package.json` +
  regenerated `package-lock.json`) and Docker base images (`infra/*.Dockerfile`,
  `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`) are
  pinned to explicit versions and monitored weekly by Dependabot
  (`.github/dependabot.yml`).
- Base images are on supported release lines (nginx 1.30 stable, Node 24 LTS,
  Python 3.12 / 3.13, PostgreSQL 17) and run `apk upgrade` / `apt-get upgrade`
  at build time to pick up OS package fixes.
- Before each deployment, run `pip-audit -r backend/requirements.txt`,
  `npm audit --omit=dev --audit-level=high` (in `frontend/`) and an image scan
  (e.g. `trivy image --severity CRITICAL,HIGH --ignore-unfixed <image>`).
  Any fixable CRITICAL/HIGH finding blocks the release.

## Accepted risks (no fix available)

| CVE | Package / image | Severity | Justification | Accepted by | Review date |
|-----|-----------------|----------|---------------|-------------|-------------|
| _none currently_ | | | | | 2027-02-25 |

Review this list at least every 90 days, or whenever a listed CVE gets a fix.
