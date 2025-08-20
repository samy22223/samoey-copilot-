# Samoey Copilot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/samy22223/samoey-copilot/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/samy22223/samoey-copilot/actions)

A unified AI-powered development platform with autonomous agents and intelligent tools that helps you write better code faster with real-time suggestions, automated fixes, and intelligent code analysis.

## 🤖 AI Team Features

### 👥 Team Roles
1. **AI Chief Architect**
   - Designs system architecture
   - Selects technology stack
   - Plans integrations

2. **Full-Stack Dev Agents**
   - Write production-ready code
   - Implement features
   - Optimize performance

3. **MLOps & AI Engineer**
   - Integrates AI models
   - Optimizes AI performance
   - Manages model deployments

4. **QA & Security Agent**
   - Runs automated tests
   - Performs security audits
   - Ensures code quality

5. **Product Manager**
   - Defines features
   - Sets priorities
   - Manages roadmap

6. **UI/UX Designer**
   - Creates responsive designs
   - Implements TailwindCSS
   - Ensures great UX

7. **Growth Hacker**
   - Integrates analytics
   - Optimizes SEO
   - Implements growth features

8. **Documentation Agent**
   - Generates documentation
   - Creates user guides
   - Maintains API docs

## 🚀 Core Features
- **AI-Powered Chat Interface**
  - Local and remote LLM support
  - Context-aware conversations
  - Code execution and analysis

- **Autonomous Development**
  - Automated code generation
  - Intelligent refactoring
  - Bug detection and fixing

- **Security & Performance**
  - Built-in security headers
  - Rate limiting
  - Performance monitoring
  - Real-time data synchronization

- **Developer Tools**
  - WebSocket API for real-time updates
  - Plugin system for extending functionality
  - Comprehensive logging and monitoring
  - Docker and Kubernetes ready

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose (recommended)
- Git
- Node.js 18 or higher
- macOS, Linux, or Windows (WSL2 recommended for Windows)

### Quick Start with Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/samy22223/samoey-copilot.git
   cd samoey-copilot
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - Web UI: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - PGAdmin: http://localhost:5050 (username: admin@samoey.local, password: admin)
   - Redis Commander: http://localhost:8081

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/samy22223/samoey-copilot.git
   cd samoey-copilot
   ```

2. Run the setup script:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```
   For development, use: `./scripts/setup.sh --dev`

3. Start the application:
   ```bash
   npm run dev
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🎯 Key Components

- **Backend**: FastAPI with WebSocket support
- **AI Integration**: LangChain, Transformers, and OpenAI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Frontend**: Next.js with TypeScript and TailwindCSS
- **Monitoring**: Built-in system metrics and health checks

## 📚 Documentation

For detailed documentation, please visit the project wiki and check the `docs/` directory.

## 🤝 Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

#### Chat Commands
- `/clear` - Clear the chat history
- `/help` - Show available commands
- `/language [en|fr]` - Change the chat language

## Configuration

Customize Samoey Copilot by editing the configuration files in the `app/config/` directory.

### `app/config/custom_instructions.json`

```json
{
    "system_prompt": "You are Samoey Copilot, an advanced AI assistant.",
    "language": "en",
    "tone": "friendly",
    "knowledge_sources": ["system"]
}
```

## Advanced Features

### AI/ML Integration

To enable local AI processing:

1. Install the required dependencies:
   ```bash
   pip install torch torchvision torchaudio
   pip install transformers sentence-transformers langchain chromadb
   ```

2. Restart the application

### API Documentation

The application provides a REST API and WebSocket interface for integration with other tools.

- **REST API**: `http://localhost:8000/api/`
- **WebSocket**: `ws://localhost:8000/ws/{client_id}`

## Troubleshooting

### Common Issues

1. **Port 3000 or 8000 is already in use**
   ```bash
   # Find and stop the process using the ports
   lsof -i :3000
   lsof -i :8000
   kill -9 <PID>
   ```

2. **Missing Dependencies**
   ```bash
   # Install all dependencies
   npm run install:all
   ```

3. **AI Features Not Working**
   - Make sure you've installed the AI/ML dependencies
   - Check the console for any error messages
   - Verify your HUGGINGFACE_TOKEN environment variable

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

## Support

For support, please open an issue on our [GitHub repository](https://github.com/samy22223/samoey-copilot/issues).
