# Setup Scripts

This directory contains various setup scripts for configuring development environments:

## Available Scripts

1. `setup_ai_environment.sh`
   - Full AI development environment setup
   - Installs Python, PyTorch, TensorFlow, and other AI/ML tools

2. `setup_ai_environment_light.sh`
   - Lightweight version of the AI environment setup
   - Minimal dependencies for basic development

3. `setup_ai_environment_macos11.sh`
   - Specialized setup for macOS 11
   - Includes compatibility fixes for older macOS versions

4. `setup_aider_simple.sh`
   - Basic setup for Aider AI coding assistant
   - Minimal dependencies

5. `setup_aider_vchat.sh`
   - Complete setup for Aider with VSCode integration
   - Includes additional developer tools and configurations

## Usage

1. Make the script executable (if needed):
   ```bash
   chmod +x script_name.sh
   ```

2. Run the desired setup script:
   ```bash
   ./script_name.sh
   ```

## Notes

- These scripts are designed for macOS but may work on other Unix-like systems with modifications.
- Always review scripts before running them, especially when using with sudo privileges.
- Some scripts may require an internet connection to download dependencies.
