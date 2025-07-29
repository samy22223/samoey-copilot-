# Pinnacle Copilot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/yourusername/pinnacle-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/pinnacle-copilot/actions)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/pinnacle-copilot)](https://hub.docker.com/r/yourusername/pinnacle-copilot)

Pinnacle Copilot is an AI-powered development assistant that helps you write better code faster with real-time suggestions, automated fixes, and intelligent code analysis.

## 🚀 Features
  - System information and health status

- **AI-Powered Chat Interface**
  - Local and remote LLM support (including OpenAI, Hugging Face, and custom models)
  - Context-aware conversations with memory
  - Support for multiple languages
  - Code execution and analysis

- **Distributed Key-Value Store**
  - Built on etcd3 for reliable distributed storage
  - High availability and fault tolerance
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
- macOS, Linux, or Windows (WSL2 recommended for Windows)

### Quick Start with Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pinnacle-copilot.git
   cd pinnacle-copilot
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PGAdmin: http://localhost:5050 (username: admin@pinnacle.local, password: admin)
   - Redis Commander: http://localhost:8081

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pinnacle-copilot.git
   cd pinnacle-copilot
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   For development, use: `./setup.sh --dev`

3. Start the application:
   ```bash
   source venv/bin/activate
   uvicorn pinnacle_copilot:app --reload
   ```

4. Access the application at http://localhost:8000

## 🎯 Key Components

- **Backend**: FastAPI with WebSocket support
- **AI Integration**: LangChain, Transformers, and OpenAI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Key-Value Store**: etcd3
- **Frontend**: HTML5, JavaScript, and WebSockets
- **Monitoring**: Built-in system metrics and health checks

## 📚 Documentation

For detailed documentation, please visit our [documentation site](https://pinnacle-copilot.readthedocs.io/).

## 🤝 Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

#### Chat Commands
- `/clear` - Clear the chat history
- `/help` - Show available commands
- `/language [en|fr]` - Change the chat language

## Configuration

Customize Pinnacle Copilot by editing the configuration files in the `config/` directory.

### `config/custom_instructions.json`

```json
{
    "system_prompt": "You are Pinnacle Copilot, an advanced AI assistant.",
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

1. **Port 8000 is already in use**
   ```bash
   # Find and stop the process using port 8000
   lsof -i :8000
   kill -9 <PID>
   ```

2. **Missing Dependencies**
   ```bash
   # Activate the virtual environment
   source venv/bin/activate
   
   # Install missing dependencies
   pip install -r requirements.txt
   ```

3. **AI Features Not Working**
   - Make sure you've installed the AI/ML dependencies
   - Check the console for any error messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

## Support

For support, please open an issue on our [GitHub repository](https://github.com/yourusername/pinnacle-copilot/issues).
