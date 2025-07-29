#!/bin/bash
set -e

# Check if .env.local exists, if not create from example
if [ ! -f .env.local ]; then
  echo "Creating .env.local from example..."
  cp .env.local.example .env.local
  
  # Generate a random secret for NextAuth
  SECRET=$(openssl rand -base64 32)
  sed -i '' "s/your-nextauth-secret-here/$SECRET/" .env.local
  
  echo "✅ .env.local created with a random NEXTAUTH_SECRET"
else
  echo "ℹ️ .env.local already exists, skipping creation"
fi

# Install dependencies
echo "Installing dependencies..."
npm install

echo "\nSetup complete! Next steps:"
echo "1. Edit .env.local with your configuration"
echo "2. Run 'npm run dev' to start the development server"
echo "3. Open http://localhost:3000 in your browser"
