#!/bin/bash
# Samoey Copilot - Ultimate 100% Completion Script
# This script completes ALL missing components automatically

set -e  # Exit on any error
set -o pipefail  # Exit if any command in pipeline fails

echo "🚀 STARTING ULTIMATE 100% COMPLETION AUTOMATION"
echo "=================================================="
echo "This will complete ALL missing components simultaneously..."
echo "Estimated time: 15-30 minutes"
echo ""

# Create logs directory
mkdir -p logs
LOG_FILE="logs/ultimate-complete-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Function to log progress
log_progress() {
    echo "[$(date '+%H:%M:%S')] $1"
}

# Phase 1: Generate ALL Missing Files (Parallel Execution)
log_progress "📁 Phase 1: Generating ALL missing files..."

{
    # Environment Files
    log_progress "  - Generating environment files..."

    # Production environment
    cat > .env.production << 'EOF'
# Production Environment Configuration

# Database
DATABASE_URL=postgresql://user:password@prod-db:5432/samoey_copilot_prod
TEST_DATABASE_URL=sqlite:///./test_prod.db

# Security
SECRET_KEY=your-production-secret-key-minimum-32-characters-change-this-in-production
OPENAI_API_KEY=your-production-openai-api-key
HUGGINGFACE_TOKEN=your-production-huggingface-token
JWT_SECRET_KEY=your-production-jwt-secret-minimum-32-characters
JWT_REFRESH_SECRET_KEY=your-production-jwt-refresh-secret-minimum-32-characters

# Redis
REDIS_URL=redis://prod-redis:6379/0
REDIS_PASSWORD=your-redis-password

# External Services
SENTRY_DSN=https://your-sentry-dsn
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-production-email@gmail.com
SMTP_PASSWORD=your-production-app-password

# AI/ML
MODEL_CACHE_DIR=/app/models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=4096
TEMPERATURE=0.7

# Monitoring
PROMETHEUS_ENDPOINT=http://prometheus:9090
GRAFANA_ENDPOINT=http://grafana:3000
LOG_LEVEL=INFO

# Performance
WORKERS=4
MAX_REQUEST_SIZE=100MB
TIMEOUT=30

# Security
SECURITY_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=50MB
ALLOWED_EXTENSIONS=txt,pdf,doc,docx,jpg,jpeg,png,gif
EOF

    # Staging environment
    cat > .env.staging << 'EOF'
# Staging Environment Configuration

# Database
DATABASE_URL=postgresql://user:password@staging-db:5432/samoey_copilot_staging
TEST_DATABASE_URL=sqlite:///./test_staging.db

# Security
SECRET_KEY=your-staging-secret-key-minimum-32-characters
OPENAI_API_KEY=your-staging-openai-api-key
HUGGINGFACE_TOKEN=your-staging-huggingface-token
JWT_SECRET_KEY=your-staging-jwt-secret-minimum-32-characters
JWT_REFRESH_SECRET_KEY=your-staging-jwt-refresh-secret-minimum-32-characters

# Redis
REDIS_URL=redis://staging-redis:6379/0
REDIS_PASSWORD=your-staging-redis-password

# External Services
SENTRY_DSN=https://your-staging-sentry-dsn
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-staging-email@gmail.com
SMTP_PASSWORD=your-staging-app-password

# AI/ML
MODEL_CACHE_DIR=/app/models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=4096
TEMPERATURE=0.7

# Monitoring
PROMETHEUS_ENDPOINT=http://staging-prometheus:9090
GRAFANA_ENDPOINT=http://staging-grafana:3000
LOG_LEVEL=DEBUG

# Performance
WORKERS=2
MAX_REQUEST_SIZE=100MB
TIMEOUT=30

# Security
SECURITY_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=200
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=https://staging.yourdomain.com

# Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=50MB
ALLOWED_EXTENSIONS=txt,pdf,doc,docx,jpg,jpeg,png,gif
EOF

    # Test environment
    cat > .env.test << 'EOF'
# Test Environment Configuration

# Database
DATABASE_URL=sqlite:///./test.db
TEST_DATABASE_URL=sqlite:///./test.db

# Security
SECRET_KEY=test-secret-key-for-testing-only-minimum-32-characters
OPENAI_API_KEY=test-openai-api-key
HUGGINGFACE_TOKEN=test-huggingface-token
JWT_SECRET_KEY=test-jwt-secret-minimum-32-characters
JWT_REFRESH_SECRET_KEY=test-jwt-refresh-secret-minimum-32-characters

# Redis
REDIS_URL=redis://localhost:6379/1
REDIS_PASSWORD=test-redis-password

# External Services
SENTRY_DSN=https://test-sentry-dsn
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=test-email@gmail.com
SMTP_PASSWORD=test-app-password

# AI/ML
MODEL_CACHE_DIR=./models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=4096
TEMPERATURE=0.7

# Monitoring
PROMETHEUS_ENDPOINT=http://localhost:9090
GRAFANA_ENDPOINT=http://localhost:3000
LOG_LEVEL=DEBUG

# Performance
WORKERS=1
MAX_REQUEST_SIZE=100MB
TIMEOUT=30

# Security
SECURITY_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=50MB
ALLOWED_EXTENSIONS=txt,pdf,doc,docx,jpg,jpeg,png,gif
EOF

    log_progress "  ✅ Environment files generated"
} &

{
    # Docker Configuration Files
    log_progress "  - Generating Docker configuration files..."

    # Test Docker Compose
    cat > docker-compose.test.yml << 'EOF'
version: '3.8'

services:
  app-test:
    build:
      context: ./app
      dockerfile: Dockerfile.test
    environment:
      - DATABASE_URL=sqlite:///./test.db
      - REDIS_URL=redis://redis-test:6379/1
      - ENVIRONMENT=test
    depends_on:
      - redis-test
    volumes:
      - ./app:/app
    command: pytest

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  frontend-test:
    build:
      context: ./frontend
      dockerfile: Dockerfile.test
    volumes:
      - ./frontend:/app
    command: npm test
EOF

    # Production Docker Compose
    cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  app-prod:
    build:
      context: ./app
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=postgresql://user:password@postgres-prod:5432/samoey_copilot_prod
      - REDIS_URL=redis://redis-prod:6379/0
      - ENVIRONMENT=production
    depends_on:
      - postgres-prod
      - redis-prod
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  frontend-prod:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    restart: unless-stopped

  postgres-prod:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=samoey_copilot_prod
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis-prod:
    image: redis:7-alpine
    volumes:
      - redis_prod_data:/data
    restart: unless-stopped

  nginx-prod:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app-prod
      - frontend-prod
    restart: unless-stopped

volumes:
  postgres_prod_data:
  redis_prod_data:
EOF

    log_progress "  ✅ Docker configuration files generated"
} &

{
    # CI/CD Workflows
    log_progress "  - Generating CI/CD workflows..."

    mkdir -p .github/workflows

    # Main CI workflow
    cat > .github/workflows/ci.yml << 'EOF'
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run backend tests
      run: |
        python -m pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/github_actions
        REDIS_URL: redis://localhost:6379/0

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: backend
        name: codecov-backend

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install frontend dependencies
      working-directory: ./frontend
      run: npm ci

    - name: Run frontend tests
      working-directory: ./frontend
      run: npm test

    - name: Run linting
      run: |
        black --check app/
        flake8 app/
        mypy app/

    - name: Security scan
      run: |
        bandit -r app/
        safety check
EOF

    # CD workflow
    cat > .github/workflows/cd.yml << 'EOF'
name: Continuous Deployment

on:
  push:
    branches: [ main ]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to Staging
      run: |
        echo "Deploying to staging environment..."
        # Add your deployment commands here

  deploy-production:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: deploy-staging

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to Production
      run: |
        echo "Deploying to production environment..."
        # Add your deployment commands here
EOF

    # Security scan workflow
    cat > .github/workflows/security-scan.yml << 'EOF'
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  security-scan:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Run security scan
      run: |
        pip install bandit safety
        bandit -r app/ -f json -o bandit-report.json
        safety check --json --output safety-report.json

    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
EOF

    log_progress "  ✅ CI/CD workflows generated"
} &

{
    # Documentation
    log_progress "  - Generating documentation..."

    # API Documentation
    cat > docs/api/README.md << 'EOF'
# Samoey Copilot API Documentation

## Base URL
- Production: `https://api.samoey-copilot.com`
- Staging: `https://staging-api.samoey-copilot.com`
- Development: `http://localhost:8000`

## Authentication
All API endpoints require authentication using Bearer tokens.

### Getting a Token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "your-password"}'
```

## Endpoints

### Authentication
#### POST /auth/login
User login endpoint.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

#### POST /auth/register
User registration endpoint.

#### POST /auth/refresh
Refresh access token endpoint.

### Chat
#### POST /chat/message
Send a chat message.

#### GET /chat/history
Get chat history.

#### WebSocket /ws/chat
Real-time chat connection.

### Users
#### GET /users/
List all users.

#### POST /users/
Create a new user.

#### GET /users/me
Get current user information.

#### PUT /users/me
Update current user information.

#### DELETE /users/{user_id}
Delete a user.

### Files
#### POST /files/upload
Upload a file.

#### GET /files/{file_id}
Download a file.

#### DELETE /files/{file_id}
Delete a file.

### Notifications
#### GET /notifications/
Get user notifications.

#### POST /notifications/mark-read
Mark notifications as read.

### Analytics
#### GET /analytics/usage
Get usage analytics.

#### GET /analytics/performance
Get performance metrics.
EOF

    # Setup Documentation
    cat > docs/setup/installation.md << 'EOF'
# Installation Guide

## Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL 15+
- Redis 7+

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/samy22223/samoey-copilot.git
cd samoey-copilot
```

### 2. Run Setup Script
```bash
./scripts/setup.sh --dev
```

### 3. Start Development Servers
```bash
npm run dev
```

### 4. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Manual Setup

### Environment Configuration
1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```env
DATABASE_URL=postgresql://user:password@localhost/samoey_copilot
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
REDIS_URL=redis://localhost:6379/0
```

### Database Setup
```bash
# Create database
createdb samoey_copilot

# Run migrations
npm run migrate

# Seed database (optional)
python app/init_data.py
```

### Install Dependencies
```bash
# Install all dependencies
npm run install:all

# Or install separately
npm install
cd frontend && npm install
cd ../app && pip install -r requirements.txt
```

### Start Services
```bash
# Start all services
npm run dev

# Or start individually
npm run dev:frontend  # Frontend on port 3000
npm run dev:backend   # Backend on port 8000
```

## Docker Setup

### Development
```bash
npm run docker:dev
```

### Production
```bash
npm run docker:prod
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Make sure ports 3000 and 8000 are available
   - Check for existing services using these ports

2. **Database Connection**
   - Verify PostgreSQL is running
   - Check database URL in `.env` file
   - Ensure database exists

3. **Redis Connection**
   - Verify Redis is running
   - Check Redis URL in `.env` file

4. **Missing Dependencies**
   - Run `npm run install:all`
   - Check for permission issues

### Getting Help

- Check the logs in `logs/` directory
- Review documentation in `docs/` directory
- Open an issue on GitHub
EOF

    log_progress "  ✅ Documentation generated"
} &

{
    # Missing Backend API Endpoints
    log_progress "  - Generating missing backend API endpoints..."

    mkdir -p app/api/v1

    # Users API
    cat > app/api/v1/users.py << 'EOF'
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserInDB, UserPublic
from app.core.security import get_current_active_user, get_password_hash
from app.core.security_metrics import security_metrics

router = APIRouter()

@router.get("/", response_model=List[UserPublic])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve all users."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserPublic)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new user."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    security_metrics.record_security_event("user_created", "info")
    return db_user

@router.get("/me", response_model=UserPublic)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user."""
    return current_user

@router.put("/me", response_model=UserPublic)
async def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update current user."""
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    security_metrics.record_security_event("user_updated", "info")
    return current_user

@router.get("/{user_id}", response_model=UserPublic)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete user."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    security_metrics.record_security_event("user_deleted", "warning")
    return None
EOF

    # Files API
    cat > app/api/v1/files.py << 'EOF'
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.core.security import get_current_active_user
from app.services.file_storage import FileStorageService
import os

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file."""
    try:
        file_service = FileStorageService()
        file_info = await file_service.save_file(file, current_user.id)
        return {
            "message": "File uploaded successfully",
            "file_id": file_info["file_id"],
            "filename": file_info["filename"],
            "size": file_info["size"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{file_id}")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download a file."""
    try:
        file_service = FileStorageService()
        file_path = await file_service.get_file_path(file_id, current_user.id)
        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a file."""
    try:
        file_service = FileStorageService()
        success = await file_service.delete_file(file_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")

        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def list_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List user files."""
    try:
        file_service = FileStorageService()
        files = await file_service.list_user_files(current_user.id, skip, limit)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
EOF

    # Notifications API
    cat > app/api/v1/notifications.py << 'EOF'
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.core.security import get_current_active_user
from app.services.notification import NotificationService

router = APIRouter()

@router.get("/")
async def get_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user notifications."""
    try:
        notification_service = NotificationService()
        notifications = await notification_service.get_user_notifications(
            current_user.id, skip, limit, unread_only
        )
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mark-read")
async def mark_notifications_read(
    notification_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark notifications as read."""
    try:
        notification_service = NotificationService()
        await notification_service.mark_notifications_read(
            current_user.id, notification_ids
        )
        return {"message": "Notifications marked as read"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a notification."""
    try:
        notification_service = NotificationService()
        success = await notification_service.delete_notification(
            current_user.id, notification_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {"message": "Notification deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
EOF

    # Analytics API
    cat > app/api/v1/analytics.py << 'EOF'
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models import User, Message, Conversation
from app.core.security import get_current_active_user
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/usage")
async def get_usage_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get usage analytics."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get message count over time
        message_counts = db.query(
            func.date(Message.created_at).label('date'),
            func.count(Message.id).label('count')
        ).filter(
            Message.created_at >= start_date,
            Message.conversation.has(Conversation.user_id == current_user.id)
        ).group_by(
            func.date(Message.created_at)
        ).all()

        # Get conversation count over time
        conversation_counts = db.query(
            func.date(Conversation.created_at).label('date'),
            func.count(Conversation.id).label('count')
        ).filter(
            Conversation.created_at >= start_date,
            Conversation.user_id == current_user.id
        ).group_by(
            func.date(Conversation.created_at)
        ).all()

        return {
            "message_counts": [
                {"date": str(item.date), "count": item.count}
                for item in message_counts
            ],
            "conversation_counts": [
                {"date": str(item.date), "count": item.count}
                for item in conversation_counts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/performance")
async def get_performance_metrics(
#!/bin/bash
# Samoey Copilot - Ultimate 100% Completion Script
# This script completes ALL missing components automatically

set -e  # Exit on any error
set -o pipefail  # Exit if any command in pipeline fails

echo "🚀 STARTING ULTIMATE 100% COMPLETION AUTOMATION"
echo "=================================================="
echo "This will complete ALL missing components simultaneously..."
echo "Estimated time: 15-30 minutes"
echo ""

# Create logs directory
mkdir -p logs
LOG_FILE="logs/ultimate-complete-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Function to log progress
log_progress() {
    echo "[$(date '+%H:%M:%S')] $1"
}

# Phase 1: Generate ALL Missing Files (Parallel Execution)
log_progress "📁 Phase 1: Generating ALL missing files..."

{
    # Environment Files
    log_progress "  - Generating environment files..."

    # Production environment
    cat > .env.production << 'EOF'
# Production Environment Configuration

# Database
DATABASE_URL=postgresql://user:password@prod-db:5432/samoey_copilot_prod
TEST_DATABASE_URL=sqlite:///./test_prod.db

# Security
SECRET_KEY=your-production-secret-key-minimum-32-characters-change-this-in-production
OPENAI_API_KEY=your-production-openai-api-key
HUGGINGFACE_TOKEN=your-production-huggingface-token
JWT_SECRET_KEY=your-production-jwt-secret-minimum-32-characters
JWT_REFRESH_SECRET_KEY=your-production-jwt-refresh-secret-minimum-32-characters

# Redis
REDIS_URL=redis://prod-redis:6379/0
REDIS_PASSWORD=your-redis-password

# External Services
SENTRY_DSN=https://your-sentry-dsn
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-production-email@gmail.com
SMTP_PASSWORD=your-production-app-password

# AI/ML
MODEL_CACHE_DIR=/app/models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=4096
TEMPERATURE=0.7

# Monitoring
PROMETHEUS_ENDPOINT=http://prometheus:9090
GRAFANA_ENDPOINT=http://grafana:3000
LOG_LEVEL=INFO

# Performance
WORKERS=4
MAX_REQUEST_SIZE=100MB
TIMEOUT=30

# Security
SECURITY_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=50MB
ALLOWED_EXTENSIONS=txt,pdf,doc,docx,jpg,jpeg,png,gif
EOF

    # Staging environment
    cat > .env.staging << 'EOF'
# Staging Environment Configuration

# Database
DATABASE_URL=postgresql://user:password@staging-db:5432/samoey_copilot_staging
TEST_DATABASE_URL=sqlite:///./test_staging.db

# Security
SECRET_KEY=your-staging-secret-key-minimum-32-characters
OPENAI_API_KEY=your-staging-openai-api-key
HUGGINGFACE_TOKEN=your-staging-huggingface-token
JWT_SECRET_KEY=your-staging-jwt-secret-minimum-32-characters
JWT_REFRESH_SECRET_KEY=your-staging-jwt-refresh-secret-minimum-32-characters

# Redis
REDIS_URL=redis://staging-redis:6379/0
REDIS_PASSWORD=your-staging-redis-password

# External Services
SENTRY_DSN=https://your-staging-sentry-dsn
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-staging-email@gmail.com
SMTP_PASSWORD=your-staging-app-password

# AI/ML
MODEL_CACHE_DIR=/app/models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=4096
TEMPERATURE=0.7

# Monitoring
PROMETHEUS_ENDPOINT=http://staging-prometheus:9090
GRAFANA_ENDPOINT=http://staging-grafana:3000
LOG_LEVEL=DEBUG

# Performance
WORKERS=2
MAX_REQUEST_SIZE=100MB
TIMEOUT=30

# Security
SECURITY_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=200
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=https://staging.yourdomain.com

# Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=50MB
ALLOWED_EXTENSIONS=txt,pdf,doc,docx,jpg,jpeg,png,gif
EOF

    # Test environment
    cat > .env.test << 'EOF'
# Test Environment Configuration

# Database
DATABASE_URL=sqlite:///./test.db
TEST_DATABASE_URL=sqlite:///./test.db

# Security
SECRET_KEY=test-secret-key-for-testing-only-minimum-32-characters
OPENAI_API_KEY=test-openai-api-key
HUGGINGFACE_TOKEN=test-huggingface-token
JWT_SECRET_KEY=test-jwt-secret-minimum-32-characters
JWT_REFRESH_SECRET_KEY=test-jwt-refresh-secret-minimum-32-characters

# Redis
REDIS_URL=redis://localhost:6379/1
REDIS_PASSWORD=test-redis-password

# External Services
SENTRY_DSN=https://test-sentry-dsn
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=test-email@gmail.com
SMTP_PASSWORD=test-app-password

# AI/ML
MODEL_CACHE_DIR=./models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=4096
TEMPERATURE=0.7

# Monitoring
PROMETHEUS_ENDPOINT=http://localhost:9090
GRAFANA_ENDPOINT=http://localhost:3000
LOG_LEVEL=DEBUG

# Performance
WORKERS=1
MAX_REQUEST_SIZE=100MB
TIMEOUT=30

# Security
SECURITY_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=50MB
ALLOWED_EXTENSIONS=txt,pdf,doc,docx,jpg,jpeg,png,gif
EOF

    log_progress "  ✅ Environment files generated"
} &

{
    # Docker Configuration Files
    log_progress "  - Generating Docker configuration files..."

    # Test Docker Compose
    cat > docker-compose.test.yml << 'EOF'
version: '3.8'

services:
  app-test:
    build:
      context: ./app
      dockerfile: Dockerfile.test
    environment:
      - DATABASE_URL=sqlite:///./test.db
      - REDIS_URL=redis://redis-test:6379/1
      - ENVIRONMENT=test
    depends_on:
      - redis-test
    volumes:
      - ./app:/app
    command: pytest

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  frontend-test:
    build:
      context: ./frontend
      dockerfile: Dockerfile.test
    volumes:
      - ./frontend:/app
    command: npm test
EOF

    # Production Docker Compose
    cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  app-prod:
    build:
      context: ./app
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=postgresql://user:password@postgres-prod:5432/samoey_copilot_prod
      - REDIS_URL=redis://redis-prod:6379/0
      - ENVIRONMENT=production
    depends_on:
      - postgres-prod
      - redis-prod
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  frontend-prod:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    restart: unless-stopped

  postgres-prod:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=samoey_copilot_prod
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis-prod:
    image: redis:7-alpine
    volumes:
      - redis_prod_data:/data
    restart: unless-stopped

  nginx-prod:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app-prod
      - frontend-prod
    restart: unless-stopped

volumes:
  postgres_prod_data:
  redis_prod_data:
EOF

    log_progress "  ✅ Docker configuration files generated"
} &

{
    # CI/CD Workflows
    log_progress "  - Generating CI/CD workflows..."

    mkdir -p .github/workflows

    # Main CI workflow
    cat > .github/workflows/ci.yml << 'EOF'
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run backend tests
      run: |
        python -m pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/github_actions
        REDIS_URL: redis://localhost:6379/0

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: backend
        name: codecov-backend

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install frontend dependencies
      working-directory: ./frontend
      run: npm ci

    - name: Run frontend tests
      working-directory: ./frontend
      run: npm test

    - name: Run linting
      run: |
        black --check app/
        flake8 app/
        mypy app/

    - name: Security scan
      run: |
        bandit -r app/
        safety check
EOF

    # CD workflow
    cat > .github/workflows/cd.yml << 'EOF'
name: Continuous Deployment

on:
  push:
    branches: [ main ]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to Staging
      run: |
        echo "Deploying to staging environment..."
        # Add your deployment commands here

  deploy-production:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: deploy-staging

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to Production
      run: |
        echo "Deploying to production environment..."
        # Add your deployment commands here
EOF

    # Security scan workflow
    cat > .github/workflows/security-scan.yml << 'EOF'
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  security-scan:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Run security scan
      run: |
        pip install bandit safety
        bandit -r app/ -f json -o bandit-report.json
        safety check --json --output safety-report.json

    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
EOF

    log_progress "  ✅ CI/CD workflows generated"
} &

{
    # Documentation
    log_progress "  - Generating documentation..."

    # API Documentation
    cat > docs/api/README.md << 'EOF'
# Samoey Copilot API Documentation

## Base URL
- Production: `https://api.samoey-copilot.com`
- Staging: `https://staging-api.samoey-copilot.com`
- Development: `http://localhost:8000`

## Authentication
All API endpoints require authentication using Bearer tokens.

### Getting a Token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "your
