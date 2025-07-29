#!/bin/bash

# Create frontend .env.local
FRONTEND_ENV="frontend/.env.local"
if [ ! -f "$FRONTEND_ENV" ]; then
  cat > "$FRONTEND_ENV" <<EOL
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=$(openssl rand -base64 32)

# Development
NODE_ENV=development
EOL
  echo "Created $FRONTEND_ENV"
else
  echo "$FRONTEND_ENV already exists, skipping"
fi

# Make the script executable
chmod +x setup-env.sh

echo "\nSetup complete! Next steps:"
echo "1. Start the backend WebSocket server: cd backend && npm install && npm start"
echo "2. In a new terminal, start the frontend: cd frontend && npm run dev"
echo "3. Open http://localhost:3000/ws-test in your browser to test the WebSocket connection"
