# VSCode Development Setup Guide

This guide provides a comprehensive setup for VSCode to enable real-time preview and optimal development experience for the Samoey Copilot project.

## 🚀 Features Enabled

### Real-Time Preview Capabilities
- **Live Server**: Real-time browser preview with hot reload
- **Browser Preview**: Embedded browser preview within VSCode
- **WebSocket Support**: Real-time communication for live updates
- **Proxy Configuration**: Seamless API integration between frontend and backend

### Enhanced Development Experience
- **Full-Stack Debugging**: Simultaneous frontend and backend debugging
- **IntelliSense**: Advanced code completion and suggestions
- **Code Formatting**: Automatic formatting with Prettier and Black
- **Linting**: Real-time error detection and fixing
- **Git Integration**: Enhanced version control features

## 📦 Required Extensions

The following extensions are automatically recommended and can be installed from the Extensions view:

### Real-Time Preview & Live Development
- `ritwickdey.LiveServer` - Live development server
- `ms-vsliveshare.vsliveshare` - Real-time collaboration
- `auchenberg.vscode-browser-preview` - Browser preview in VSCode
- `yosiayalon.vscode-preview-server` - Preview server
- `ms-vscode.live-server` - Microsoft Live Server
- `wix.vscode-import-cost` - Import package size visualization
- `christian-kohler.path-intellisense` - Path autocompletion

### Frontend Development
- `msjsdiag.vscode-react-native` - React Native tools
- `ms-vscode.vscode-typescript-next` - Next.js support
- `pranaygp.vscode-css-peek` - CSS peek functionality
- `formulahendry.auto-rename-tag` - Auto rename HTML/XML tags
- `Zignd.html-css-class-completion` - CSS class completion
- `bradlc.vscode-tailwindcss` - Tailwind CSS IntelliSense
- `esbenp.prettier-vscode` - Prettier code formatter
- `dbaeumer.vscode-eslint` - ESLint integration
- `ms-vscode.vscode-html-preview` - HTML preview
- `bierner.markdown-preview-github-styles` - GitHub-style markdown
- `shd101wyy.markdown-preview-enhanced` - Enhanced markdown preview

### Python Backend
- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Python IntelliSense
- `ms-python.test-adapter-python` - Python test adapter
- `ms-python.debugpy` - Python debugger
- `ms-toolsai.jupyter` - Jupyter notebook support
- `ms-python.black-formatter` - Black code formatter
- `ms-python.isort` - Import sorter
- `kevinrose.vsc-python-indent` - Python indentation
- `njpwerner.autodocstring` - Auto docstring generation
- `donjayamanne.python-environment-manager` - Python environment management

### Docker & DevOps
- `ms-azuretools.vscode-docker` - Docker extension
- `ms-vscode-remote.remote-containers` - Remote containers
- `ms-kubernetes-tools.vscode-kubernetes-tools` - Kubernetes tools
- `redhat.vscode-yaml` - YAML language support

### Code Quality & Analysis
- `SonarSource.sonarlint-vscode` - SonarLint code analysis
- `streetsidesoftware.code-spell-checker` - Spell checker
- `eamodio.gitlens` - Enhanced Git capabilities
- `usernamehw.errorlens` - Error highlighting
- `ms-vscode.vscode-json` - JSON language support
- `redhat.vscode-xml` - XML language support
- `shd101wyy.markdown-all-in-one` - Markdown tools

### Database & API
- `mtxr.sqltools` - Database management
- `mtxr.sqltools-driver-pg` - PostgreSQL driver
- `mtxr.sqltools-driver-redis` - Redis driver
- `humao.rest-client` - REST client
- `rangav.vscode-thunder-client` - Thunder Client API testing
- `Prisma.prisma` - Prisma ORM support
- `cweijan.vscode-redis-client` - Redis client

### AI & Productivity
- `github.copilot` - GitHub Copilot AI assistant
- `github.copilot-chat` - Copilot chat interface
- `TabNine.tabnine-vscode` - TabNine AI completion
- `formulahendry.code-runner` - Code runner
- `alefragnani.Bookmarks` - Bookmark management
- `Gruntfuggly.todo-tree` - TODO management
- `wakatime.vscode-wakatime` - Time tracking
- `vscode-icons-team.vscode-icons` - File icons

### Testing & Debugging
- `ms-vscode.vscode-js-debug` - JavaScript debugger
- `ms-playwright.playwright` - Playwright testing
- `hbenl.vscode-test-explorer` - Test explorer
- `ms-vscode.test-adapter-converter` - Test adapter converter

### Git & Version Control
- `mhutchie.git-graph` - Git graph visualization
- `donjayamanne.githistory` - Git history
- `waderyan.gitblame` - Git blame annotations

### Terminal & Shell
- `ms-vscode.vscode-terminal` - Terminal enhancements
- `Tyriar.vscode-shellcheck` - Shell script linting
- `timonwong.shellcheck` - Shell script analysis

### Theme & Interface
- `Equinusocio.vsc-material-theme` - Material theme
- `PKief.material-icon-theme` - Material icon theme
- `drcika.apc-extension` - Activity bar customization

## 🛠️ Launch Configurations

### Available Debug Configurations

1. **Launch Frontend (Next.js Dev)** - Starts Next.js development server
2. **Launch Backend (FastAPI)** - Starts FastAPI development server
3. **Debug Frontend (Chrome)** - Debug frontend with Chrome DevTools
4. **Debug Backend (Python)** - Attach Python debugger
5. **Launch Full Stack (Dev Mode)** - Start both frontend and backend
6. **Debug Tests (Frontend)** - Run frontend tests in debug mode
7. **Debug Tests (Backend)** - Run backend tests in debug mode
8. **Docker Compose Up (Dev)** - Start Docker development environment
9. **Docker Compose Down** - Stop Docker environment

### Compound Configurations

- **Debug Full Stack** - Simultaneously debug both frontend and backend
- **Debug All Tests** - Run all tests in debug mode

## 📋 Available Tasks

### Development Tasks
- `Install All Dependencies` - Install all project dependencies
- `Start Frontend Dev Server` - Start Next.js development server
- `Start Backend Dev Server` - Start FastAPI development server
- `Start Full Stack Dev` - Start both frontend and backend
- `Open Live Server` - Start live server for real-time preview

### Build Tasks
- `Build Frontend` - Build frontend for production
- `Build Backend` - Build backend for production
- `Build All` - Build entire project
- `Run Database Migration` - Apply database migrations
- `Create Database Migration` - Generate new migration

### Testing Tasks
- `Run Frontend Tests` - Run frontend test suite
- `Run Backend Tests` - Run backend test suite
- `Run All Tests` - Run all project tests
- `Lint Frontend` - Lint frontend code
- `Lint Backend` - Lint backend code
- `Format Code` - Format all code with Prettier/Black

### Docker Tasks
- `Start Docker Dev Environment` - Start Docker containers
- `Stop Docker Environment` - Stop Docker containers

### Maintenance Tasks
- `Clean Node Modules` - Clean and reinstall node modules
- `Clean Python Cache` - Clean Python cache files
- `Setup Development Environment` - Run initial setup script
- `Generate API Documentation` - Generate API docs

## 🌐 Real-Time Preview Setup

### Method 1: Live Server (Recommended)

1. **Start Live Server**:
   - Use command palette: `Tasks: Run Task`
   - Select `Open Live Server`
   - Live server will start on `http://localhost:3001`

2. **Start Development Servers**:
   - Use command palette: `Tasks: Run Task`
   - Select `Start Full Stack Dev`
   - This will start both frontend (port 3000) and backend (port 8000)

3. **Configure Proxy**:
   - Live server is configured to proxy API requests from `/api` to `http://localhost:8000`
   - This allows seamless communication between frontend and backend

### Method 2: Browser Preview

1. **Start Development Servers**:
   - Use command palette: `Tasks: Run Task`
   - Select `Start Full Stack Dev`

2. **Open Browser Preview**:
   - Right-click any HTML file and select "Browser Preview: Open"
   - Or use command palette: `Browser Preview: Open`

3. **Configure Preview**:
   - Browser preview is configured to start at `http://localhost:3000`
   - API requests are proxied to `http://localhost:8000`

### Method 3: External Browser with Live Reload

1. **Start Frontend Development Server**:
   - Use command palette: `Tasks: Run Task`
   - Select `Start Frontend Dev Server`
   - Frontend will be available at `http://localhost:3000`

2. **Start Backend Development Server**:
   - Use command palette: `Tasks: Run Task`
   - Select `Start Backend Dev Server`
   - Backend API will be available at `http://localhost:8000`

3. **Enable Live Reload**:
   - The frontend server includes hot reload functionality
   - Changes to frontend code will automatically refresh the browser
   - Changes to backend code will restart the server

## 🔧 Key Settings

### Editor Configuration
- Format on save: Enabled
- Auto save: Enabled (1 second delay)
- Auto closing brackets/quotes: Enabled
- Sticky scroll: Enabled
- Bracket pair colorization: Enabled

### Language Support
- **Python**: Strict type checking, Black formatting, pytest testing
- **TypeScript/JavaScript**: Auto imports, inlay hints, ESLint integration
- **Tailwind CSS**: IntelliSense, class completion, color decorators
- **Docker**: Compose support, container management

### Real-Time Preview Settings
- Live Server port: 3001
- Live Server root: `/frontend`
- Browser Preview port: 3000
- Proxy configuration: `/api` → `http://localhost:8000`

## 🚀 Quick Start

1. **Install Extensions**:
   - Open VSCode
   - Go to Extensions view
   - Click "Show Recommended Extensions"
   - Install all recommended extensions

2. **Setup Environment**:
   ```bash
   # Run the setup task
   # Command Palette > Tasks: Run Task > Setup Development Environment
   ```

3. **Start Development**:
   ```bash
   # Option 1: Full stack development
   # Command Palette > Tasks: Run Task > Start Full Stack Dev

   # Option 2: Real-time preview
   # Command Palette > Tasks: Run Task > Open Live Server
   # Command Palette > Tasks: Run Task > Start Full Stack Dev
   ```

4. **Open Browser**:
   - Navigate to `http://localhost:3001` (Live Server)
   - Or `http://localhost:3000` (Direct Next.js)

## 🐛 Debugging

### Frontend Debugging
1. Set breakpoints in TypeScript/JavaScript files
2. Use "Debug Frontend (Chrome)" configuration
3. Debug using Chrome DevTools within VSCode

### Backend Debugging
1. Set breakpoints in Python files
2. Use "Debug Backend (Python)" configuration
3. Debug using Python debugger

### Full Stack Debugging
1. Use "Debug Full Stack" compound configuration
2. Debug both frontend and backend simultaneously
3. Switch between debug sessions as needed

## 📝 Tips and Tricks

### Productivity
- Use `Ctrl+Shift+P` to access command palette
- Use `Ctrl+P` for quick file navigation
- Use `Ctrl+`` to open integrated terminal
- Use `Ctrl+Shift+`` to create new terminal

### Real-Time Development
- Live Server provides instant preview updates
- WebSocket support enables real-time features
- Proxy configuration handles API routing automatically
- Hot reload works for both frontend and backend changes

### Code Quality
- Code is automatically formatted on save
- ESLint and Pylint provide real-time feedback
- Error Lens highlights issues directly in the editor
- Spell checking ensures documentation quality

## 🔍 Troubleshooting

### Common Issues

**Live Server not working**:
- Check if port 3001 is available
- Ensure Live Server extension is installed
- Verify task configuration in tasks.json

**Backend not starting**:
- Check Python virtual environment setup
- Verify dependencies are installed
- Check port 8000 availability

**Frontend not building**:
- Check Node.js version compatibility
- Verify npm dependencies
- Clear Next.js cache: `rm -rf .next`

**Extension conflicts**:
- Disable conflicting extensions
- Check extension settings
- Restart VSCode after configuration changes

### Getting Help

1. Check VSCode output panel for error messages
2. Review terminal output for task execution details
3. Consult extension documentation for specific issues
4. Verify all system requirements are met

## 📋 System Requirements

- **VSCode**: Latest version recommended
- **Node.js**: v16+ for frontend
- **Python**: v3.8+ for backend
- **Docker**: Optional, for containerized development
- **Memory**: 8GB+ recommended for full-stack development
- **Storage**: 2GB+ free space for dependencies

---

This setup provides a comprehensive development environment with real-time preview capabilities, enabling efficient full-stack development for the Samoey Copilot project.
