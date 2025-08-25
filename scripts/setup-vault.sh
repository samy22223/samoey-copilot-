#!/bin/bash

# Vault Setup Script for Samoey Copilot
# Implements enterprise-grade secrets management

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VAULT_VERSION="1.14.0"
VAULT_CONFIG_DIR="./vault-config"
SEED_FILE="$VAULT_CONFIG_DIR/vault-seed.json"
ENVIRONMENT=${1:-development}

echo -e "${BLUE}🔐 Setting up Vault for Samoey Copilot - Environment: $ENVIRONMENT${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p "$VAULT_CONFIG_DIR/logs"
mkdir -p "$VAULT_CONFIG_DIR/file"
mkdir -p "$VAULT_CONFIG_DIR/plugins"

# Generate root token if not exists
if [ ! -f "$SEED_FILE" ]; then
    echo -e "${YELLOW}🔑 Generating Vault root token...${NC}"
    ROOT_TOKEN="vault-$(head -c 16 /dev/urandom | od -An -t x | tr -d ' \n')"

    cat > "$SEED_FILE" << EOF
{
  "root_token": "$ROOT_TOKEN",
  "environment": "$ENVIRONMENT",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "unseal_keys": []
}
EOF

    echo -e "${GREEN}✅ Root token generated and saved to $SEED_FILE${NC}"
else
    ROOT_TOKEN=$(jq -r '.root_token' "$SEED_FILE")
    echo -e "${GREEN}📋 Using existing root token from $SEED_FILE${NC}"
fi

# Start Vault container
echo -e "${YELLOW}🚀 Starting Vault container...${NC}"
docker run -d \
    --name samoey-vault \
    --cap-add=IPC_LOCK \
    -p 8200:8200 \
    -p 8201:8201 \
    -v "$VAULT_CONFIG_DIR:/vault/config" \
    -v "$VAULT_CONFIG_DIR/file:/vault/file" \
    -v "$VAULT_CONFIG_DIR/logs:/vault/logs" \
    -v "$VAULT_CONFIG_DIR/plugins:/vault/plugins" \
    -e "VAULT_ADDR=http://0.0.0.0:8200" \
    -e "VAULT_API_ADDR=http://0.0.0.0:8200" \
    -e "VAULT_CLUSTER_ADDR=https://0.0.0.0:8201" \
    hashicorp/vault:$VAULT_VERSION server \
    -config=/vault/config/vault-config.hcl

# Wait for Vault to start
echo -e "${YELLOW}⏳ Waiting for Vault to start...${NC}"
sleep 10

# Check if Vault is running
if ! docker exec samoey-vault vault status > /dev/null 2>&1; then
    echo -e "${RED}❌ Failed to start Vault container${NC}"
    docker logs samoey-vault
    exit 1
fi

# Initialize Vault if not already initialized
echo -e "${YELLOW}🔧 Initializing Vault...${NC}"
if ! docker exec samoey-vault vault status | grep -q "Initialized.*true"; then
    INIT_OUTPUT=$(docker exec samoey-vault vault operator init -key-shares=5 -key-threshold=3 -format=json)

    # Extract unseal keys and root token
    UNSEAL_KEYS=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[]')
    NEW_ROOT_TOKEN=$(echo "$INIT_OUTPUT" | jq -r '.root_token')

    # Save unseal keys to seed file
    jq --arg keys "$UNSEAL_KEYS" '.unseal_keys = ($keys | split("\n") | map(select(. != "")))' "$SEED_FILE" > "$SEED_FILE.tmp" && mv "$SEED_FILE.tmp" "$SEED_FILE"
    jq --arg token "$NEW_ROOT_TOKEN" '.root_token = $token' "$SEED_FILE" > "$SEED_FILE.tmp" && mv "$SEED_FILE.tmp" "$SEED_FILE"

    echo -e "${GREEN}✅ Vault initialized successfully${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Unseal keys have been saved to $SEED_FILE${NC}"
    echo -e "${YELLOW}⚠️  Keep this file secure and back it up!${NC}"
else
    echo -e "${GREEN}✅ Vault already initialized${NC}"
fi

# Unseal Vault
echo -e "${YELLOW}🔓 Unsealing Vault...${NC}"
UNSEAL_KEYS=$(jq -r '.unseal_keys[]' "$SEED_FILE")
for key in $UNSEAL_KEYS; do
    if [ -n "$key" ]; then
        docker exec samoey-vault vault operator unseal "$key"
    fi
done

# Export Vault token for commands
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="$ROOT_TOKEN"

# Wait a moment for unsealing to complete
sleep 5

# Configure Vault
echo -e "${YELLOW}⚙️  Configuring Vault...${NC}"

# Enable audit logging
docker exec samoey-vault vault audit enable file file_path=/vault/logs/audit.log

# Enable necessary secrets engines
docker exec samoey-vault vault secrets enable -path=secret kv-v2
docker exec samoey-vault vault secrets enable -path=database database
docker exec samoey-vault vault secrets enable -path=pki pki

# Configure PKI for internal TLS
docker exec samoey-vault vault write pki/root/generate/internal \
    common_name="Samoey Copilot Internal CA" \
    ttl=87600h

docker exec samoey-vault vault write pki/roles/samoey-internal \
    allowed_domains="samoey.local,localhost" \
    allow_subdomains=true \
    max_ttl=720h

# Create policies for different environments
echo -e "${YELLOW}📋 Creating access policies...${NC}"

# Development policy
cat > /tmp/dev-policy.hcl << EOF
# Development environment policy
path "secret/data/development/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "database/creds/development-*" {
  capabilities = ["read"]
}

path "pki/issue/samoey-internal" {
  capabilities = ["create", "update"]
}
EOF

# Production policy
cat > /tmp/prod-policy.hcl << EOF
# Production environment policy
path "secret/data/production/*" {
  capabilities = ["read", "list"]
}

path "secret/data/production/config" {
  capabilities = ["create", "read", "update"]
}

path "database/creds/production-*" {
  capabilities = ["read"]
}

path "pki/issue/samoey-internal" {
  capabilities = ["create", "update"]
}
EOF

# Admin policy
cat > /tmp/admin-policy.hcl << EOF
# Admin policy
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
EOF

# Write policies to Vault
docker exec -i samoey-vault vault policy write development /tmp/dev-policy.hcl
docker exec -i samoey-vault vault policy write production /tmp/prod-policy.hcl
docker exec -i samoey-vault vault policy write admin /tmp/admin-policy.hcl

# Enable userpass auth method
docker exec samoey-vault vault auth enable userpass

# Create users for different environments
echo -e "${YELLOW}👤 Creating users...${NC}"

# Development user
DEV_PASSWORD=$(head -c 12 /dev/urandom | od -An -t x | tr -d ' \n')
docker exec samoey-vault vault write auth/userpass/users/dev \
    password="$DEV_PASSWORD" \
    policies=development

# Production user
PROD_PASSWORD=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' \n')
docker exec samoey-vault vault write auth/userpass/users/prod \
    password="$PROD_PASSWORD" \
    policies=production

# Admin user
ADMIN_PASSWORD=$(head -c 20 /dev/urandom | od -An -t x | tr -d ' \n')
docker exec samoey-vault vault write auth/userpass/users/admin \
    password="$ADMIN_PASSWORD" \
    policies=admin

# Store application secrets
echo -e "${YELLOW}🔐 Storing application secrets...${NC}"

# Database credentials
docker exec samoey-vault vault write secret/data/$ENVIRONMENT/database \
    host="localhost" \
    port="5432" \
    username="samoey_app" \
    password=$(head -c 24 /dev/urandom | od -An -t x | tr -d ' \n') \
    database="samoey_copilot" \
    ssl_mode="require"

# API keys
docker exec samoey-vault vault write secret/data/$ENVIRONMENT/api \
    openai_api_key="sk-placeholder-openai-key" \
    huggingface_token="hf-placeholder-huggingface-token" \
    jwt_secret=$(head -c 32 /dev/urandom | od -An -t x | tr -d ' \n') \
    encryption_key=$(head -c 64 /dev/urandom | od -An -t x | tr -d ' \n')

# Monitoring credentials
docker exec samoey-vault vault write secret/data/$ENVIRONMENT/monitoring \
    grafana_admin_password=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' \n') \
    prometheus_password=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' \n')

# Create environment-specific credentials file
cat > "$VAULT_CONFIG_DIR/credentials-$ENVIRONMENT.json" << EOF
{
  "vault_addr": "http://localhost:8200",
  "vault_token": "$ROOT_TOKEN",
  "users": {
    "dev": {
      "username": "dev",
      "password": "$DEV_PASSWORD"
    },
    "prod": {
      "username": "prod",
      "password": "$PROD_PASSWORD"
    },
    "admin": {
      "username": "admin",
      "password": "$ADMIN_PASSWORD"
    }
  },
  "environment": "$ENVIRONMENT",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# Clean up temporary files
rm -f /tmp/dev-policy.hcl /tmp/prod-policy.hcl /tmp/admin-policy.hcl

echo -e "${GREEN}✅ Vault setup completed successfully!${NC}"
echo -e "${BLUE}📋 Summary:${NC}"
echo -e "  - Vault UI: http://localhost:8200"
echo -e "  - Root Token: $ROOT_TOKEN"
echo -e "  - Environment: $ENVIRONMENT"
echo -e "  - Credentials saved to: $VAULT_CONFIG_DIR/credentials-$ENVIRONMENT.json"
echo -e "  - Seed file: $SEED_FILE"
echo -e "${YELLOW}⚠️  IMPORTANT: Secure the seed file and credentials!${NC}"

# Generate environment file for application
echo -e "${YELLOW}📝 Generating environment file...${NC}"
cat > ".env.vault" << EOF
# Vault Configuration for Samoey Copilot
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=$ROOT_TOKEN
VAULT_ENVIRONMENT=$ENVIRONMENT

# Application Secrets (will be fetched from Vault)
# These are placeholders - actual secrets should be fetched at runtime
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=samoey_app
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET=$(head -c 32 /dev/urandom | od -An -t x | tr -d ' \n')
ENCRYPTION_KEY=$(head -c 64 /dev/urandom | od -An -t x | tr -d ' \n')
EOF

echo -e "${GREEN}✅ Environment file created: .env.vault${NC}"
echo -e "${BLUE}🎯 Next steps:${NC}"
echo -e "  1. Update your application to use Vault for secrets management"
echo -e "  2. Set up automatic secret rotation"
echo -e "  3. Configure Vault monitoring and alerts"
echo -e "  4. Set up Vault backup and disaster recovery"
