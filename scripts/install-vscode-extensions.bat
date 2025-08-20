@echo off
REM VSCode Extensions Installer for Samoey Copilot (Windows)
REM This script automatically installs all recommended VSCode extensions

echo 🚀 Installing VSCode Extensions for Samoey Copilot
echo ==================================================

REM Check if VSCode is installed
where code >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ VSCode is not installed. Please install VSCode first.
    echo    Download from: https://code.visualstudio.com/
    pause
    exit /b 1
)

echo ✅ VSCode found
for /f "tokens=*" %%a in ('code --version ^| findstr /r "^"') do (
    echo    %%a
    goto :break_version
)
:break_version

REM Array of all recommended extensions
set extensions=^
ritwickdey.LiveServer^
ms-vsliveshare.vsliveshare^
auchenberg.vscode-browser-preview^
yosiayalon.vscode-preview-server^
ms-vscode.live-server^
wix.vscode-import-cost^
christian-kohler.path-intellisense^
msjsdiag.vscode-react-native^
ms-vscode.vscode-typescript-next^
pranaygp.vscode-css-peek^
formulahendry.auto-rename-tag^
Zignd.html-css-class-completion^
bradlc.vscode-tailwindcss^
esbenp.prettier-vscode^
dbaeumer.vscode-eslint^
ms-vscode.vscode-html-preview^
bierner.markdown-preview-github-styles^
shd101wyy.markdown-preview-enhanced^
ms-python.python^
ms-python.vscode-pylance^
ms-python.test-adapter-python^
ms-python.debugpy^
ms-toolsai.jupyter^
ms-python.black-formatter^
ms-python.isort^
kevinrose.vsc-python-indent^
njpwerner.autodocstring^
donjayamanne.python-environment-manager^
ms-azuretools.vscode-docker^
ms-vscode-remote.remote-containers^
ms-kubernetes-tools.vscode-kubernetes-tools^
redhat.vscode-yaml^
SonarSource.sonarlint-vscode^
streetsidesoftware.code-spell-checker^
eamodio.gitlens^
usernamehw.errorlens^
ms-vscode.vscode-json^
redhat.vscode-xml^
shd101wyy.markdown-all-in-one^
mtxr.sqltools^
mtxr.sqltools-driver-pg^
mtxr.sqltools-driver-redis^
humao.rest-client^
rangav.vscode-thunder-client^
Prisma.prisma^
cweijan.vscode-redis-client^
github.copilot^
github.copilot-chat^
TabNine.tabnine-vscode^
formulahendry.code-runner^
alefragnani.Bookmarks^
Gruntfuggly.todo-tree^
wakatime.vscode-wakatime^
vscode-icons-team.vscode-icons^
ms-vscode.vscode-js-debug^
ms-playwright.playwright^
hbenl.vscode-test-explorer^
ms-vscode.test-adapter-converter^
mhutchie.git-graph^
donjayamanne.githistory^
waderyan.gitblame^
ms-vscode.vscode-terminal^
Tyriar.vscode-shellcheck^
timonwong.shellcheck^
Equinusocio.vsc-material-theme^
PKief.material-icon-theme^
drcika.apc-extension

REM Count extensions
set count=0
for %%e in (%extensions%) do (
    set /a count+=1
)

echo 📦 Found %count% extensions to install
echo.

REM Initialize counters
set installed=0
set already_installed=0
set failed=0

REM Install each extension
for %%e in (%extensions%) do (
    set /p "=🔄 Installing %%e... " <nul

    REM Try to install with force first
    code --install-extension %%e --force >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Installed
        set /a installed+=1
    ) else (
        REM If force fails, try without force
        code --install-extension %%e >nul 2>&1
        if !errorlevel! equ 0 (
            echo ⚠️  Already installed
            set /a already_installed+=1
        ) else (
            echo ❌ Failed to install
            set /a failed+=1
        )
    )
)

echo.
echo 🎉 Installation Complete!
echo ========================
echo ✅ Successfully installed: %installed%
echo ⚠️  Already installed: %already_installed%
echo ❌ Failed to install: %failed%

if %failed% gtr 0 (
    echo.
    echo ⚠️  Some extensions failed to install. This might be due to:
    echo    • Network connectivity issues
    echo    • Extension not being available in the marketplace
    echo    • VSCode marketplace being temporarily unavailable
    echo.
    echo 💡 You can try installing the failed extensions manually:
    echo    1. Open VSCode
    echo    2. Go to Extensions view (Ctrl+Shift+X)
    echo    3. Search for and install each failed extension
)

echo.
echo 🔄 Reloading VSCode window to apply changes...
start /b code --reload-window

echo.
echo 💡 Next Steps:
echo    1. Restart VSCode if it doesn't reload automatically
echo    2. Open the workspace: samoey-copilot-realtime-preview.code-workspace
echo    3. Start real-time preview with: scripts\start-realtime-preview.bat
echo    4. Or use VSCode tasks: Ctrl+Shift+P ^> 'Tasks: Run Task' ^> 'Start Real-Time Preview'
echo.
echo 🎯 Your VSCode is now ready for real-time development!

pause
