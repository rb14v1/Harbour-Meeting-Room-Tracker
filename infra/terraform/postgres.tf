# Azure Database for PostgreSQL Flexible Server for manojasdyg-82692.
# Automated backups: 30-day retention, geo-redundant (paired region) copies and
# point-in-time recovery (PITR), which the flexible server enables with backups.
# Restore procedure: docs/RESTORE.md

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

variable "resource_group_name" {
  type        = string
  description = "Resource group that holds the PostgreSQL server."
}

variable "location" {
  type        = string
  description = "Primary Azure region. Geo-redundant backups go to its paired region."
}

variable "administrator_login" {
  type        = string
  description = "PostgreSQL administrator login."
}

variable "administrator_password" {
  type        = string
  sensitive   = true
  description = "PostgreSQL administrator password. Supply via TF_VAR_administrator_password."
}

variable "sku_name" {
  type        = string
  default     = "B_Standard_B1ms"
  description = "Server SKU."
}

variable "storage_mb" {
  type        = number
  default     = 32768
  description = "Storage size in MB."
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                = "psql-manojasdyg-82692"
  resource_group_name = var.resource_group_name
  location            = var.location
  version             = "17"

  administrator_login    = var.administrator_login
  administrator_password = var.administrator_password

  sku_name   = var.sku_name
  storage_mb = var.storage_mb

  # Automated backups with PITR over the whole retention window.
  backup_retention_days = 30

  # Backups are replicated to the paired region, separate from the primary.
  # This can only be set when the server is created.
  geo_redundant_backup_enabled = true

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_postgresql_flexible_server_database" "meeting_rooms" {
  name      = "meeting_rooms"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

output "postgresql_server_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}
