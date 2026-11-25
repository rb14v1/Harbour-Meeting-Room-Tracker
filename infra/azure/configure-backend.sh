#!/usr/bin/env bash
# One-time, re-runnable runtime configuration for the backend Container App.
# Secrets are stored as Container App secrets and referenced by name.
#
#   export RESOURCE_GROUP=manojasdyg-82692 BACKEND_APP=manojasdyg-82692-backend
#   export DB_HOST=<postgresql_host terraform output> DB_PASSWORD=<postgresql_password output>
#   export DJANGO_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
#   export FRONTEND_ORIGIN=https://<frontend-fqdn>
#   bash infra/azure/configure-backend.sh
set -euo pipefail

: "${RESOURCE_GROUP:?}" "${BACKEND_APP:?}" "${DB_HOST:?}" "${DB_PASSWORD:?}" \
  "${DJANGO_SECRET_KEY:?}" "${FRONTEND_ORIGIN:?}"
DB_USER="${DB_USER:-psqladmin}"
DB_NAME="${DB_NAME:-postgres}"

az extension add --name containerapp --upgrade --only-show-errors

fqdn=$(az containerapp show -n "$BACKEND_APP" -g "$RESOURCE_GROUP" \
  --query properties.configuration.ingress.fqdn -o tsv)

az containerapp ingress update -n "$BACKEND_APP" -g "$RESOURCE_GROUP" \
  --target-port 8080 --only-show-errors

az containerapp secret set -n "$BACKEND_APP" -g "$RESOURCE_GROUP" \
  --secrets "db-password=${DB_PASSWORD}" "django-secret-key=${DJANGO_SECRET_KEY}" \
  --only-show-errors

az containerapp update -n "$BACKEND_APP" -g "$RESOURCE_GROUP" --only-show-errors \
  --set-env-vars \
    DJANGO_DEBUG=0 \
    DJANGO_BEHIND_PROXY=1 \
    DJANGO_ALLOWED_HOSTS="$fqdn" \
    CORS_ALLOWED_ORIGINS="$FRONTEND_ORIGIN" \
    CSRF_TRUSTED_ORIGINS="https://$fqdn" \
    DB_HOST="$DB_HOST" DB_PORT=5432 DB_NAME="$DB_NAME" DB_USER="$DB_USER" \
    DB_SSLMODE=require APP_TIME_ZONE=Asia/Kolkata \
    DB_PASSWORD=secretref:db-password \
    DJANGO_SECRET_KEY=secretref:django-secret-key

echo "Backend configured: https://$fqdn"
