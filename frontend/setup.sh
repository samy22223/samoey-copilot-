#!/bin/bash
set -e

echo "🚀 Setting up Pinnacle Copilot Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and try again."
    echo "🔗 https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm and try again."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18 or higher is required. Current version: $(node -v)"
    exit 1
fi

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📄 Creating .env.local file..."
    cp .env.local.example .env.local
    
    # Generate a random secret for NextAuth
    SECRET=$(openssl rand -base64 32)
    sed -i '' "s/your-secret-here/$SECRET/" .env.local
    
    echo "✅ .env.local created with a random NEXTAUTH_SECRET"
else
    echo "ℹ️ .env.local already exists, skipping creation"
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Set up Git hooks
echo "🔧 Setting up Git hooks..."
npx husky install

# Build the project
echo "🏗️  Building the project..."
npm run build

echo "✨ Setup complete!"
echo "🚀 Start the development server with: npm run dev"
echo "🌐 Open http://localhost:3000 in your browser"
