# Pinnacle Copilot Frontend

This is the frontend for Pinnacle Copilot, an AI-powered development assistant.

## Features

- Real-time chat interface
- Code syntax highlighting
- Dark/light mode
- Responsive design
- PWA support (installable on devices)
- Offline capabilities

## Prerequisites

- Node.js 18+ and npm 9+
- Next.js 14
- TypeScript 5+

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pinnacle-copilot.git
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.local.example .env.local
   ```
   Update the `.env.local` file with your configuration.

4. **Run the development server**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm start` - Start the production server
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## Environment Variables

Create a `.env.local` file in the root directory with the following variables:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-here

# Optional: Google OAuth
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_SECRET=

# Optional: GitHub OAuth
# GITHUB_CLIENT_ID=
# GITHUB_CLIENT_SECRET=
```

## Project Structure

```
frontend/
├── public/              # Static files
├── src/
│   ├── app/             # App router
│   ├── components/      # Reusable components
│   ├── contexts/        # React contexts
│   ├── hooks/           # Custom hooks
│   ├── lib/             # Utility functions
│   ├── services/        # API and WebSocket services
│   └── styles/          # Global styles
├── .env.local.example   # Example environment variables
├── next.config.js       # Next.js configuration
└── package.json         # Dependencies and scripts
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
