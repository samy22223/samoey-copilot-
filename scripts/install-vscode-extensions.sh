#!/bin/bash

# VSCode Extensions Installer for Samoey Copilot
# This script automatically installs all recommended VSCode extensions

set -e

echo "🚀 Installing VSCode Extensions for Samoey Copilot"
echo "=================================================="

# Check if VSCode is installed
if ! command -v code &> /dev/null; then
    echo "❌ VSCode is not installed. Please install VSCode first."
    echo "   Download from: https://code.visualstudio.com/"
    exit 1
fi

echo "✅ VSCode found: $(code --version | head -n 1)"

# Array of all recommended extensions
extensions=(
    # Real-Time Preview & Live Development
    "ritwickdey.LiveServer"
    "ms-vsliveshare.vsliveshare"
    "auchenberg.vscode-browser-preview"
    "yosiayalon.vscode-preview-server"
    "ms-vscode.live-server"
    "wix.vscode-import-cost"
    "christian-kohler.path-intellisense"

    # Frontend Development
    "msjsdiag.vscode-react-native"
    "ms-vscode.vscode-typescript-next"
    "pranaygp.vscode-css-peek"
    "formulahendry.auto-rename-tag"
    "Zignd.html-css-class-completion"
    "bradlc.vscode-tailwindcss"
    "esbenp.prettier-vscode"
    "dbaeumer.vscode-eslint"
    "ms-vscode.vscode-html-preview"
    "bierner.markdown-preview-github-styles"
    "shd101wyy.markdown-preview-enhanced"

    # Python Backend
    "ms-python.python"
    "ms-python.vscode-pylance"
    "ms-python.test-adapter-python"
    "ms-python.debugpy"
    "ms-toolsai.jupyter"
    "ms-python.black-formatter"
    "ms-python.isort"
    "kevinrose.vsc-python-indent"
    "njpwerner.autodocstring"
    "donjayamanne.python-environment-manager"

    # Docker & DevOps
    "ms-azuretools.vscode-docker"
    "ms-vscode-remote.remote-containers"
    "ms-kubernetes-tools.vscode-kubernetes-tools"
    "redhat.vscode-yaml"

    # Code Quality & Analysis
    "SonarSource.sonarlint-vscode"
    "streetsidesoftware.code-spell-checker"
    "eamodio.gitlens"
    "usernamehw.errorlens"
    "ms-vscode.vscode-json"
    "redhat.vscode-xml"
    "shd101wyy.markdown-all-in-one"

    # Database & API
    "mtxr.sqltools"
    "mtxr.sqltools-driver-pg"
    "mtxr.sqltools-driver-redis"
    "humao.rest-client"
    "rangav.vscode-thunder-client"
    "Prisma.prisma"
    "cweijan.vscode-redis-client"

    # AI & Productivity
    "github.copilot"
    "github.copilot-chat"
    "TabNine.tabnine-vscode"
    "formulahendry.code-runner"
    "alefragnani.Bookmarks"
    "Gruntfuggly.todo-tree"
    "wakatime.vscode-wakatime"
    "vscode-icons-team.vscode-icons"

    # Testing & Debugging
    "ms-vscode.vscode-js-debug"
    "ms-playwright.playwright"
    "hbenl.vscode-test-explorer"
    "ms-vscode.test-adapter-converter"

    # Git & Version Control
    "mhutchie.git-graph"
    "donjayamanne.githistory"
    "waderyan.gitblame"

    # Terminal & Shell
    "ms-vscode.vscode-terminal"
    "Tyriar.vscode-shellcheck"
    "timonwong.shellcheck"

    # Theme & Interface
    "Equinusocio.vsc-material-theme"
    "PKief.material-icon-theme"
    "drcika.apc-extension"
)

echo "📦 Found ${#extensions[@]} extensions to install"
echo ""

# Counters
installed=0
already_installed=0
failed=0

# Install each extension
for extension in "${extensions[@]}"; do
    echo -n "🔄 Installing $extension... "

    if code --install-extension "$extension" --force &> /dev/null; then
        echo "✅ Installed"
        ((installed++))
    elif code --install-extension "$extension" &> /dev/null; then
        echo "⚠️  Already installed"
        ((already_installed++))
    else
        echo "❌ Failed to install"
        ((failed++))
    fi
done

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo "✅ Successfully installed: $installed"
echo "⚠️  Already installed: $already_installed"
echo "❌ Failed to install: $failed"

if [ $failed -gt 0 ]; then
    echo ""
    echo "⚠️  Some extensions failed to install. This might be due to:"
    echo "   • Network connectivity issues"
    echo "   • Extension not being available in the marketplace"
    echo "   • VSCode marketplace being temporarily unavailable"
    echo ""
    echo "💡 You can try installing the failed extensions manually:"
    echo "   1. Open VSCode"
    echo "   2. Go to Extensions view (Ctrl+Shift+X)"
    echo "   3. Search for and install each failed extension"
fi

echo ""
echo "🔄 Reloading VSCode window to apply changes..."
code --reload-window &

echo ""
echo "💡 Next Steps:"
echo "   1. Restart VSCode if it doesn't reload automatically"
echo "   2. Open the workspace: samoey-copilot-realtime-preview.code-workspace"
echo "   3. Start real-time preview with: ./scripts/start-realtime-preview.sh"
echo "   4. Or use VSCode tasks: Ctrl+Shift+P > 'Tasks: Run Task' > 'Start Real-Time Preview'"
echo ""
echo "🎯 Your VSCode is now ready for real-time development!"
