# RISC Git Auto Commit & Push Tool

This tool is an automated Git commit and push helper script that integrates Azure OpenAI. It analyzes your git diff (including newly added files) and generates concise, structured commit messages per category. If the AI cannot determine the CPU, machine, or type fields, it will prompt you to select or enter them manually, ensuring a safe and efficient workflow.

## Features

- **Automatic Analysis**: Analyzes git diff (including new/untracked files) and generates standardized commit messages in the format `[cpu][machine][type] title`.
- **Category Separation**: Automatically detects and separates changes into DTS, CONFIG, DRIVERS, and SCRIPT categories, and commits them separately.
- **Manual or Free-form Selection**: Prompts you to either pick from a list or freely enter CPU, machine type, or change type if the AI cannot determine them.
- **Flexible Push**: Allows you to choose whether to push after committing.
- **Azure OpenAI Integration**: Summarizes diff content and produces clear commit messages using Azure OpenAI.
- **Fully Automated Staging**: New/untracked files are detected and automatically added to staging before commit.

## Requirements

- Python 3
- git
- [requests](https://pypi.org/project/requests/) Python package (`pip install requests`)
- Azure OpenAI API Key and Endpoint

## Setup

1. Download the script: `risc_git_auto_pushes_commit.py`
2. Set up environment variables (recommended: in `.bashrc`, `.zshrc`, or before running the script):
   ```bash
   export OPENAI_API_KEY="your-azure-openai-api-key"
   export OPENAI_ENDPOINT="your-azure-openai-endpoint"
   ```
3. Install Python dependencies:
   ```bash
   pip install requests
   ```

## Usage

1. Change into your git repository directory.
2. Run:
   ```bash
   python3 risc_git_auto_pushes_commit.py /path/to/your/repo
   ```
   or make the script executable and run:
   ```bash
   ./risc_git_auto_pushes_commit.py /path/to/your/repo
   ```
3. The script will:
   - Automatically detect and stage new/untracked files.
   - Detect changes, categorize by type, and call Azure OpenAI to generate commit messages.
   - If the AI cannot determine certain fields, you will be prompted to select from a list or freely enter a value.
   - Review each proposed commit message and confirm before committing.
   - After all commits, you will be asked if you want to push to the remote.

## Commit Message Example

```
[imx8mp][ROM-5722][script] Update build scripts for ROM5722A2

- Replace ROM5722A1 with ROM5722A2 in build scripts
- Update build condition and command
```

## Supported Types (but not limited to)

- **CPU**: imx8mm, imx8mp, imx93, or any value you wish to input
- **Machine**: ROM-5721, ROM-5722, ROM-2820, or any value you wish to input
- **Type**: dts, drivers, config, kconfig, script, or any value you wish to input

If the AI cannot determine a value, you can always enter your own.

## FAQ

- **API Key/Endpoint not set?**
  > The script will prompt you to export both environment variables.
- **AI returns "unknown"?**
  > The script will prompt you to select or enter the correct CPU, machine, or type manually.
- **No changes detected?**
  > The script will exit without performing any commit or push.
- **New files not committed?**
  > New/untracked files are automatically staged and included in the commit process.

## Contribution

Feel free to submit issues, pull requests, or contact the author for improvements.

---