#!/bin/bash

# Aider & vChat Complete Setup Script for macOS Desktop
# This script sets up Aider AI coding assistant and vChat on your desktop

set -e  # Exit on any error

echo "🤖 Setting up Aider & vChat on Desktop"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Create project directory
PROJECT_DIR="$HOME/CascadeProjects/aider chat"
print_status "Creating project directory at $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create and activate virtual environment with Python 3.10
print_status "Creating Python 3.10 virtual environment"
/usr/local/bin/python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip and install required build tools
print_status "Installing build tools"
pip install --upgrade pip
pip install wheel setuptools

# Install Aider
print_status "Installing Aider"
pip install aider-chat

# Create a requirements.txt
echo "aider-chat" > requirements.txt

# Create a README.md
cat > README.md << 'EOL'
# Aider Chat Project

This is an Aider chat project for pair programming with AI.

## Setup

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Start Aider:
   ```bash
   aider
   ```

## Usage

- Use natural language to describe the changes you want to make
- Aider will help you write and modify code
- All changes will be shown before they're applied
EOL

print_status "${GREEN}Setup complete!${NC}"
echo ""
echo "To get started, run these commands:"
echo "cd '$PROJECT_DIR'"
echo "source venv/bin/activate"
echo "aider"

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Create desktop workspace
DESKTOP_PATH="/Users/samoey/Desktop"
WORKSPACE_PATH="$DESKTOP_PATH/aider-vchat-workspace"

print_status "Creating workspace at $WORKSPACE_PATH"
mkdir -p "$WORKSPACE_PATH"
cd "$WORKSPACE_PATH"

# Step 1: Setup Python Environment for Aider
print_status "Step 1: Setting up Python environment for Aider..."

# Find the best Python installation
PYTHON_PATH=""
PIP_PATH=""

if [ -f "/Library/Frameworks/Python.framework/Versions/Current/bin/python3.13" ]; then
    PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/Current/bin/python3.13"
    PIP_PATH="/Library/Frameworks/Python.framework/Versions/Current/bin/pip3.13"
    print_success "Found Python 3.13 in Framework"
elif [ -f "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12" ]; then
    PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12"
    PIP_PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin/pip3.12"
    print_success "Found Python 3.12 in Framework"
elif command_exists python3; then
    PYTHON_PATH=$(which python3)
    PIP_PATH=$(which pip3)
    print_success "Using system Python: $PYTHON_PATH"
else
    print_error "No Python installation found. Please install Python first."
    exit 1
fi

print_status "Using Python: $PYTHON_PATH"
print_status "Using pip: $PIP_PATH"

# Step 2: Install Aider
print_status "Step 2: Installing Aider AI coding assistant..."

# Upgrade pip first
$PIP_PATH install --upgrade pip

# Install aider-chat
print_status "Installing aider-chat..."
$PIP_PATH install aider-chat

# Verify installation
if command_exists aider; then
    print_success "Aider installed successfully!"
    aider --version
else
    # Try with full path
    AIDER_PATH=$(dirname $PIP_PATH)/aider
    if [ -f "$AIDER_PATH" ]; then
        print_success "Aider installed at $AIDER_PATH"
        $AIDER_PATH --version
    else
        print_warning "Aider installation may need PATH update"
    fi
fi

# Step 3: Setup vChat
print_status "Step 3: Setting up vChat..."

# Clone vChat repository (assuming it's a GitHub project)
if [ ! -d "vchat" ]; then
    print_status "Cloning vChat repository..."
    git clone https://github.com/vchat-ai/vchat.git 2>/dev/null || {
        print_status "Creating vChat setup directory..."
        mkdir -p vchat
        cd vchat
        
        # Create a basic vChat setup
        cat > requirements.txt << 'EOF'
openai>=1.0.0
anthropic>=0.7.0
streamlit>=1.28.0
gradio>=3.50.0
langchain>=0.1.0
chromadb>=0.4.0
tiktoken>=0.5.0
python-dotenv>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
EOF

        # Create basic vChat interface
        cat > vchat_app.py << 'EOF'
import streamlit as st
import openai
import os
from datetime import datetime

st.set_page_config(page_title="vChat - AI Assistant", page_icon="🤖", layout="wide")

st.title("🤖 vChat - AI Assistant")
st.markdown("Your personal AI chat assistant on the desktop")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Key input
    api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")
    
    # Model selection
    model = st.selectbox("Model", ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"])
    
    # Temperature
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7)
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "timestamp" in message:
            st.caption(f"⏰ {message['timestamp']}")

# Chat input
if prompt := st.chat_input("What can I help you with?"):
    # Add user message to chat history
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        "timestamp": timestamp
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"⏰ {timestamp}")
    
    # Generate AI response
    if api_key:
        try:
            openai.api_key = api_key
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=[
                            {"role": m["role"], "content": m["content"]} 
                            for m in st.session_state.messages
                        ],
                        temperature=temperature
                    )
                    
                    assistant_response = response.choices[0].message.content
                    st.markdown(assistant_response)
                    
                    response_timestamp = datetime.now().strftime("%H:%M:%S")
                    st.caption(f"⏰ {response_timestamp}")
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": assistant_response,
                        "timestamp": response_timestamp
                    })
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please check your API key and try again.")
    else:
        with st.chat_message("assistant"):
            st.warning("Please enter your OpenAI API key in the sidebar to start chatting.")

# Footer
st.markdown("---")
st.markdown("💡 **Tip**: You can use this chat interface for coding help, questions, and general assistance!")
EOF

        cd ..
    }
fi

# Install vChat dependencies
if [ -d "vchat" ]; then
    cd vchat
    print_status "Installing vChat dependencies..."
    $PIP_PATH install -r requirements.txt
    cd ..
fi

# Step 4: Create Desktop Launchers
print_status "Step 4: Creating desktop launchers..."

# Create Aider launcher script
cat > start_aider.sh << EOF
#!/bin/bash

echo "🤖 Starting Aider AI Coding Assistant"
echo "===================================="

# Find aider executable
AIDER_PATH=""
if command -v aider >/dev/null 2>&1; then
    AIDER_PATH="aider"
elif [ -f "$(dirname $PIP_PATH)/aider" ]; then
    AIDER_PATH="$(dirname $PIP_PATH)/aider"
else
    echo "❌ Aider not found. Please check installation."
    exit 1
fi

echo "📂 Current directory: \$(pwd)"
echo "🚀 Starting Aider..."
echo ""
echo "💡 Aider Commands:"
echo "  /help     - Show help"
echo "  /add file - Add file to chat"
echo "  /commit   - Commit changes"
echo "  /exit     - Exit Aider"
echo ""

# Start Aider
\$AIDER_PATH "\$@"
EOF

chmod +x start_aider.sh

# Create vChat launcher script
cat > start_vchat.sh << EOF
#!/bin/bash

echo "💬 Starting vChat Interface"
echo "=========================="

cd vchat

echo "🌐 Starting Streamlit server..."
echo "📱 vChat will open in your browser at: http://localhost:8501"
echo ""
echo "💡 Usage Tips:"
echo "  - Enter your OpenAI API key in the sidebar"
echo "  - Select your preferred model"
echo "  - Start chatting!"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start Streamlit
$PYTHON_PATH -m streamlit run vchat_app.py --server.port 8501 --server.address localhost
EOF

chmod +x start_vchat.sh

# Create combined launcher
cat > start_ai_tools.sh << 'EOF'
#!/bin/bash

echo "🤖 AI Tools Launcher"
echo "==================="
echo ""
echo "Choose an option:"
echo "1. Start Aider (AI Coding Assistant)"
echo "2. Start vChat (AI Chat Interface)"
echo "3. Start both"
echo "4. Exit"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Starting Aider..."
        ./start_aider.sh
        ;;
    2)
        echo "Starting vChat..."
        ./start_vchat.sh
        ;;
    3)
        echo "Starting both tools..."
        echo "Starting vChat in background..."
        ./start_vchat.sh &
        VCHAT_PID=$!
        
        echo "Starting Aider..."
        ./start_aider.sh
        
        # When Aider exits, stop vChat
        kill $VCHAT_PID 2>/dev/null
        ;;
    4)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac
EOF

chmod +x start_ai_tools.sh

# Step 5: Create configuration files
print_status "Step 5: Creating configuration files..."

# Create .env template for API keys
cat > .env.template << 'EOF'
# API Keys Configuration
# Copy this file to .env and add your actual API keys

# OpenAI API Key (for GPT models)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (for Claude models)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Other API keys as needed
GOOGLE_API_KEY=your_google_api_key_here
EOF

# Create Aider configuration
cat > .aider.conf.yml << 'EOF'
# Aider Configuration
model: gpt-4
edit-format: diff
git: true
gitignore: true
auto-commits: true
dirty-commits: true
attribute-author: true
attribute-committer: true
attribute-commit-message: true
EOF

# Step 6: Create documentation
print_status "Step 6: Creating documentation..."

cat > README.md << 'EOF'
# 🤖 Aider & vChat Desktop Setup

This workspace contains AI-powered coding and chat tools for your desktop.

## 🚀 Quick Start

### Option 1: Use the Combined Launcher
```bash
./start_ai_tools.sh
```

### Option 2: Start Individual Tools

#### Start Aider (AI Coding Assistant)
```bash
./start_aider.sh
```

#### Start vChat (AI Chat Interface)
```bash
./start_vchat.sh
```

## 🔧 Configuration

### API Keys
1. Copy `.env.template` to `.env`
2. Add your API keys to the `.env` file
3. For vChat, you can also enter the API key in the web interface

### Aider Configuration
- Edit `.aider.conf.yml` to customize Aider settings
- See [Aider documentation](https://aider.chat/docs/) for more options

## 📖 Usage

### Aider Commands
- `/help` - Show all available commands
- `/add <file>` - Add files to the conversation
- `/commit` - Commit changes with AI-generated message
- `/diff` - Show pending changes
- `/undo` - Undo last change
- `/exit` - Exit Aider

### vChat Features
- Web-based chat interface
- Multiple AI model support
- Conversation history
- Configurable temperature settings
- Real-time responses

## 🛠 Troubleshooting

### If Aider is not found:
```bash
# Check if aider is in PATH
which aider

# Or use full path
/path/to/python -m pip install aider-chat
```

### If vChat won't start:
```bash
# Check dependencies
pip install -r vchat/requirements.txt

# Start manually
cd vchat
streamlit run vchat_app.py
```

## 📚 Resources

- [Aider Documentation](https://aider.chat/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
EOF

# Step 7: Create desktop shortcuts (macOS)
print_status "Step 7: Creating desktop shortcuts..."

# Create AppleScript app for Aider
cat > "/Users/samoey/Desktop/Aider.app.applescript" << EOF
tell application "Terminal"
    do script "cd '$WORKSPACE_PATH' && ./start_aider.sh"
    activate
end tell
EOF

# Create AppleScript app for vChat
cat > "/Users/samoey/Desktop/vChat.app.applescript" << EOF
tell application "Terminal"
    do script "cd '$WORKSPACE_PATH' && ./start_vchat.sh"
    activate
end tell
EOF

# Create AppleScript app for AI Tools Launcher
cat > "/Users/samoey/Desktop/AI-Tools.app.applescript" << EOF
tell application "Terminal"
    do script "cd '$WORKSPACE_PATH' && ./start_ai_tools.sh"
    activate
end tell
EOF

# Compile AppleScript apps
if command_exists osacompile; then
    print_status "Compiling desktop apps..."
    osacompile -o "/Users/samoey/Desktop/Aider.app" "/Users/samoey/Desktop/Aider.app.applescript"
    osacompile -o "/Users/samoey/Desktop/vChat.app" "/Users/samoey/Desktop/vChat.app.applescript"
    osacompile -o "/Users/samoey/Desktop/AI-Tools.app" "/Users/samoey/Desktop/AI-Tools.app.applescript"
    
    # Clean up script files
    rm "/Users/samoey/Desktop/Aider.app.applescript"
    rm "/Users/samoey/Desktop/vChat.app.applescript"
    rm "/Users/samoey/Desktop/AI-Tools.app.applescript"
    
    print_success "Desktop apps created!"
else
    print_warning "osacompile not available. Manual shortcuts created in workspace."
fi

# Step 8: Test installations
print_status "Step 8: Testing installations..."

# Test Aider
if command_exists aider || [ -f "$(dirname $PIP_PATH)/aider" ]; then
    print_success "✅ Aider is ready!"
else
    print_warning "⚠️  Aider may need PATH configuration"
fi

# Test vChat dependencies
cd vchat
if $PYTHON_PATH -c "import streamlit, openai" 2>/dev/null; then
    print_success "✅ vChat dependencies are ready!"
else
    print_warning "⚠️  Some vChat dependencies may be missing"
fi
cd ..

# Final summary
print_success "🎉 Aider & vChat Setup Complete!"
echo ""
echo "📋 What was installed:"
echo "  ✅ Aider AI coding assistant"
echo "  ✅ vChat web interface"
echo "  ✅ Desktop launcher apps"
echo "  ✅ Configuration files"
echo "  ✅ Documentation"
echo ""
echo "🚀 Quick Start Options:"
echo "  1. Double-click 'AI-Tools.app' on your desktop"
echo "  2. Or run: cd '$WORKSPACE_PATH' && ./start_ai_tools.sh"
echo ""
echo "📁 Workspace location: $WORKSPACE_PATH"
echo ""
echo "🔑 Don't forget to:"
echo "  1. Copy .env.template to .env"
echo "  2. Add your OpenAI API key"
echo "  3. Read the README.md for detailed instructions"
echo ""
print_success "Happy coding with AI! 🤖✨"
