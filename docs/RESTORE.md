# Database Backup and Restore

## Backup configuration

The production database is the Azure Database for PostgreSQL Flexible Server `psql-meet-harb1`, defined in [`infra/terraform/postgres.tf`](../infra/terraform/postgres.tf).

| Setting | Value |
|---|---|
| Automated backups | Enabled (managed by Azure, daily snapshots plus continuous WAL archiving) |
| Retention | `backup_retention_days = 30` |
| Off-region copy | `geo_redundant_backup_enabled = true` (backups replicated to the paired region) |
| Point-in-time recovery | Any point within the last 30 days |

Check the live settings:

```powershell
az postgres flexible-server show -g <resource-group> -n psql-meet-harb1 --query "backup"
```

## Restore procedure (point-in-time recovery)

A restore always creates a **new** server. The original server is not changed.

1. Choose the restore time (UTC, ISO 8601) — just before the incident.
2. Restore to a new server in the same region:

   ```powershell
   az postgres flexible-server restore `
     -g <resource-group> `
     --name psql-meet-harb1-restore `
     --source-server psql-meet-harb1 `
     --restore-time "2026-01-01T10:00:00Z"
   ```

3. If the primary region is unavailable, restore from the geo-redundant backup into the paired region:

   ```powershell
   az postgres flexible-server geo-restore `
     -g <resource-group> `
     --name psql-meet-harb1-geo `
     --source-server psql-meet-harb1 `
     --location <paired-region>
   ```

4. Verify the restored data:

   ```powershell
   psql "host=<restored-fqdn> dbname=meeting_rooms user=<admin> sslmode=require" -c "SELECT count(*) FROM bookings;"
   ```

5. Point the backend at the restored server by setting `DB_HOST` (and `DB_PASSWORD` if changed) in the backend environment, restart the backend, then run `python healthz.py`.
6. Once confirmed, bring the restored server under Terraform (rename or `terraform import`) and decommission the old one.

Firewall rules, server parameters and Entra ID settings are not copied by a restore; re-apply them before switching traffic.

## Local / Docker databases

Local development databases are not backed up automatically. For a manual copy:

```powershell
pg_dump -U meeting_app -h localhost -d meeting_rooms -F c -f meeting_rooms_backup.dump
pg_restore -U meeting_app -h localhost -d meeting_rooms meeting_rooms_backup.dump
```

## Restore test record

A restore must be tested before go-live and at least once a year after that. Record each test here.

| Date (UTC) | Performed by | Type (PITR / geo-restore) | Restore point | Duration | Result / notes |
|---|---|---|---|---|---|
| _pending — required before go-live_ | | | | | |
