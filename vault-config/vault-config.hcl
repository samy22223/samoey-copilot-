# Vault Configuration for Samoey Copilot
# Production-ready secrets management configuration

storage "file" {
  path = "/vault/file"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

ui = true

# API settings
api_addr = "http://0.0.0.0:8200"

# Maximum lease duration
default_lease_ttl = "168h"
max_lease_ttl = "720h"

# Cluster settings (for production HA)
cluster_name = "samoey-copilot-vault"
cluster_addr = "https://127.0.0.1:8201"

# Plugin directory
plugin_directory = "/vault/plugins"

# Enable audit logging
audit {
  enabled = true
  options = {
    file = "/vault/logs/audit.log"
  }
}

# Enable telemetry
telemetry {
  disable_hostname = false
  prometheus_retention_time = "24h"
  enable_hostname_label = true
}
