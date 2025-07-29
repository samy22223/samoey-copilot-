# Code GPT Integration with Pinnacle Copilot

This guide explains how to set up and use Code GPT with Pinnacle Copilot for AI-powered code assistance.

## Prerequisites

- VS Code installed
- Code GPT extension installed in VS Code
- Pinnacle Copilot running locally

## Setup

### 1. Install the Code GPT Extension

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X or Cmd+Shift+X)
3. Search for "Code GPT"
4. Install the extension by Tim Kmecl or the official one by Daniel San

### 2. Configure Code GPT

Run the setup script to configure Code GPT:

```bash
python scripts/setup_codegpt.py
```

Or with an API key directly:

```bash
python scripts/setup_codegpt.py --api-key "your-api-key-here"
```

### 3. Restart VS Code

After configuration, restart VS Code for the changes to take effect.

## Using Code GPT with Pinnacle Copilot

### Basic Usage

1. Open any code file in VS Code
2. Select the code you want to work with
3. Right-click and choose "Code GPT: Explain Code" (or any other Code GPT command)
4. The request will be processed by Pinnacle Copilot

### Available Code GPT Commands

- **Explain Code**: Get an explanation of the selected code
- **Refactor Code**: Get suggestions for refactoring the selected code
- **Generate Tests**: Generate unit tests for the selected code
- **Find Bugs**: Analyze the code for potential bugs
- **Optimize Code**: Get optimization suggestions
- **Add Documentation**: Generate documentation for the selected code

## Advanced Configuration

You can customize the Code GPT integration by editing your VS Code settings:

1. Open VS Code settings (Ctrl+, or Cmd+,)
2. Search for "codegpt"
3. Adjust the settings as needed

### Available Settings

- `codegpt.apiKey`: Your Code GPT API key
- `codegpt.model`: The AI model to use (default: "gpt-4")
- `codegpt.temperature`: Controls randomness (0.0 to 1.0)
- `codegpt.maxTokens`: Maximum number of tokens in the response
- `codegpt.pinnacleIntegration.enabled`: Enable/disable Pinnacle Copilot integration
- `codegpt.pinnacleIntegration.endpoint`: Pinnacle Copilot API endpoint
- `codegpt.pinnacleIntegration.autoSync`: Automatically sync with Pinnacle Copilot

## Troubleshooting

### Code GPT Commands Not Appearing

1. Ensure the Code GPT extension is installed and enabled
2. Restart VS Code
3. Check the VS Code extensions view for any errors

### Connection Issues

1. Make sure Pinnacle Copilot is running
2. Verify the API endpoint in the settings
3. Check the Pinnacle Copilot logs for any errors

## Example Workflow

1. Open a Python file with some code
2. Select a function
3. Right-click and choose "Code GPT: Add Documentation"
4. Review the generated documentation
5. Choose to insert it or make changes as needed

## Security Note

Your API key is stored in your VS Code settings file. Keep this file secure and don't share it publicly.
