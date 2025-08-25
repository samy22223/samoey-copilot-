# Docker Compose Environment Usage Guide

This guide explains how to use the different environment-specific Docker Compose configurations with proper environment variable loading.

## Overview

Each environment (production, staging, test) now has its own:
- Environment file (`.env.production`, `.env.staging`, `.env.test`)
- Docker Compose file (`docker-compose.prod.yml`, `docker-compose.staging.yml`, `docker-compose.test.yml`)

## Environment Variables

Docker Compose will automatically load environment variables from the respective `.env.*` files when you use the correct compose file.

### Production Environment

**Environment File:** `.env.production`
**Compose File:** `docker-compose.prod.yml`

To run the production environment:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

To stop the production environment:
```bash
docker-compose -f docker-compose.prod.yml down
```

### Staging Environment

**Environment File:** `.env.staging`
**Compose File:** `docker-compose.staging.yml`

To run the staging environment:
```bash
docker-compose -f docker-compose.staging.yml up -d
```

To stop the staging environment:
```bash
docker-compose -f docker-compose.staging.yml down
```

### Test Environment

**Environment File:** `.env.test`
**Compose File:** `docker-compose.test.yml`

To run the test environment:
```bash
docker-compose -f docker-compose.test.yml up -d
```

To run tests:
```bash
docker-compose -f docker-compose.test.yml run --rm test-runner
```

To stop the test environment:
```bash
docker-compose -f docker-compose.test.yml down
```

## Development Environment

The main `docker-compose.yml` file is for development and uses the default `.env` file.

To run the development environment:
```bash
docker-compose up -d
```

To stop the development environment:
```bash
docker-compose down
```

## Environment Variable Management

### Adding New Variables

1. Add the variable to the appropriate `.env.*` file
2. Reference it in the corresponding Docker Compose file using `${VARIABLE_NAME}` syntax
3. Add the `env_file: - .env.*` directive to services that need the variable

### Variable Substitution

Docker Compose automatically substitutes `${VARIABLE_NAME}` with values from:
1. The environment file specified in `env_file`
2. Environment variables set in the shell
3. Default values (if specified using `${VARIABLE_NAME:-default_value}`)

### Security Notes

- Never commit sensitive environment variables to version control
- Use `.env.example` as a template for required variables
- Keep production environment files secure and restricted
- Consider using Docker secrets for highly sensitive data in production

## Common Issues and Solutions

### Environment Variables Not Loading

**Symptom:** `${VARIABLE_NAME}` appears as literal text instead of being substituted

**Solution:** Ensure you're using the correct compose file with the corresponding env file:
```bash
# Correct
docker-compose -f docker-compose.prod.yml up

# Incorrect (won't load .env.production)
docker-compose -f docker-compose.prod.yml --env-file .env.production up
```

### Missing Variables

**Symptom:** Error about undefined environment variables

**Solution:**
1. Check that the variable exists in the correct `.env.*` file
2. Ensure the service has `env_file: - .env.*` directive
3. Verify the variable name matches exactly (case-sensitive)

### Port Conflicts

**Symptom:** Port already in use errors

**Solution:** Each environment uses different ports:
- Production: DB=5435, Redis=6382, App=3003/8003
- Staging: DB=5434, Redis=6381, App=3002/8002
- Test: DB=5433, Redis=6380, App=3001/8001
- Development: DB=5432, Redis=6379, App=3000/8000

## Best Practices

1. **Environment Isolation:** Each environment has its own network, volumes, and ports
2. **Variable Naming:** Use consistent naming across environments
3. **File Organization:** Keep environment-specific files clearly named
4. **Documentation:** Document any new environment variables added
5. **Testing:** Test environment variable loading in each environment

## Troubleshooting

To verify environment variables are loaded correctly:

```bash
# Check specific environment
docker-compose -f docker-compose.prod.yml exec prod-app env | grep DATABASE_URL

# View all environment variables for a service
docker-compose -f docker-compose.prod.yml exec prod-app env
```

## File Structure

```
├── .env                    # Development environment
├── .env.production         # Production environment
├── .env.staging           # Staging environment
├── .env.test              # Test environment
├── docker-compose.yml     # Development compose
├── docker-compose.prod.yml # Production compose
├── docker-compose.staging.yml # Staging compose
└── docker-compose.test.yml # Test compose
