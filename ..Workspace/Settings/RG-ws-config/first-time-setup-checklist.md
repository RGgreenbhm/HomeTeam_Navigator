# First-Time Setup Checklist
**Repository:** Patient_Explorer  
**Last Verified:** December 2, 2025  
**Purpose:** One-time verification that development environment is properly configured

---

## ✅ Core Development Tools

| Tool | Required Version | Installed | Status | Notes |
|------|-----------------|-----------|--------|-------|
| **Python** | 3.10+ | 3.12.2 | ✅ READY | Core runtime for Streamlit app |
| **pip** | Latest | 24.0 | ✅ READY | Python package manager |
| **Node.js** | 20.0+ | 25.0.0 | ✅ READY | Needed for archive/electron (optional) |
| **npm** | Latest | 11.6.2 | ✅ READY | Node package manager |
| **Git** | 2.x+ | 2.52.0 | ✅ READY | Version control |
| **VS Code** | Latest | 1.106.3 | ✅ READY | Primary IDE |
| **PowerShell** | 7.x+ | 7.5.4 | ✅ READY | Default shell & scripting |

---

## ✅ Required VS Code Extensions

| Extension | ID | Installed | Purpose |
|-----------|----|-----------|----- ---|
| **Python** | `ms-python.python` | ✅ YES | Python language support |
| **Pylance** | `ms-python.vscode-pylance` | ✅ YES | Python IntelliSense |
| **Python Debugger** | `ms-python.debugpy` | ✅ YES | Python debugging |
| **PowerShell** | `ms-vscode.powershell` | ✅ YES | PowerShell support |
| **GitHub Copilot** | `github.copilot` | ✅ YES | AI code assistance |
| **GitHub Copilot Chat** | `github.copilot-chat` | ✅ YES | AI chat interface (includes Claude Code) |

---

## 🤖 Claude Code Chat Interface

**Status:** ✅ READY (via GitHub Copilot Chat)

Claude Code is available through GitHub Copilot Chat with the following setup:

### Current Configuration
- **Extension:** GitHub Copilot Chat (installed)
- **Custom Commands:** 17 custom slash commands configured in `.claude/commands/`
- **Settings:** Local permissions configured in `.claude/settings.local.json`
- **Model Access:** Claude Sonnet 4.5 via Copilot Chat interface

### How to Use Claude Code
1. Open Copilot Chat panel in VS Code (Ctrl+Alt+I or Cmd+Alt+I)
2. Select "Claude 3.5 Sonnet" from model picker
3. Use custom slash commands from `.claude/commands/` folder
4. Workspace context is automatically available via `CLAUDE.md` and copilot-instructions

### Custom Commands Available
- `/bmad-analyst` - Business analyst mode
- `/bmad-architect` - Architecture design mode
- `/bmad-dev` - Development mode
- `/bmad-qa` - Quality assurance mode
- `/bmad-pm` - Project management mode
- `/workspace-brief` - Generate daily workspace brief
- `/save-chat` - Save chat transcript
- And 10 more specialized commands

### Workspace Context Files
- `.github/copilot-instructions.md` - Project-specific guidance for AI
- `CLAUDE.md` - AI assistant guidance (552 lines)
- `README.md` - Project overview
- `.claude/settings.local.json` - Command permissions

**Note:** Claude Code functionality is built into GitHub Copilot Chat. No separate extension needed.

---

## 📦 Recommended VS Code Extensions

| Extension | ID | Installed | Purpose |
|-----------|----|-----------|----- ---|
| **Streamlit Runner** | `joshrmosier.streamlit-runner` | ❌ NO | Run Streamlit apps from context menu |
| **Markdown All in One** | `yzhang.markdown-all-in-one` | ❌ NO | Enhanced markdown editing |
| **markdownlint** | `davidanson.vscode-markdownlint` | ❌ NO | Markdown style checking |

**Install recommended extensions:**
```powershell
code --install-extension joshrmosier.streamlit-runner
code --install-extension yzhang.markdown-all-in-one
code --install-extension davidanson.vscode-markdownlint
```

---

## ⚠️ Optional Cloud Tools (Not Required)

| Tool | Status | Purpose | Install If Needed |
|------|--------|---------|-------------------|
| **Azure CLI** | ❌ NOT INSTALLED | Azure resource management | [Download](https://aka.ms/installazurecliwindows) |
| **.NET SDK** | ❌ NOT INSTALLED | C# development (not needed for Python) | [Download](https://dotnet.microsoft.com/download) |
| **GitHub CLI** | ❌ NOT INSTALLED | GitHub operations from CLI | [Download](https://cli.github.com/) |
| **Docker Desktop** | ❓ UNKNOWN | Containerization (not needed for local dev) | [Download](https://www.docker.com/products/docker-desktop) |

---

## 🔧 Project-Specific Setup

### 1. Python Virtual Environment
**Status:** ❌ NOT CREATED

**Action Required:**
```powershell
# Run from repository root
.\setup-beta.ps1
```

This will:
- Create `.venv/` directory
- Install all Python dependencies from `requirements.txt`
- Initialize SQLite database
- Create `.env` template file

### 2. Environment Variables
**Status:** ⚠️ NEEDS CONFIGURATION

**File:** `.env` (will be created by setup script)

**Required Variables:**
```env
# Spruce Health API (for SMS outreach)
SPRUCE_API_TOKEN=your_token_here
SPRUCE_ACCESS_ID=your_access_id_here

# Microsoft Forms (for consent tracking)
MS_FORMS_BASE_URL=https://forms.office.com/...

# Azure/Claude AI (optional, for AI features)
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_API_KEY=your_key_here
```

### 3. Windows Security Requirements
**Status:** ⚠️ VERIFY MANUALLY

**Required for HIPAA Compliance:**
- [ ] Windows 11 installed
- [ ] BitLocker encryption enabled on system drive
- [ ] Windows Defender active
- [ ] Automatic updates enabled

**Verify BitLocker:**
```powershell
Get-BitLockerVolume -MountPoint "C:"
```

---

## 📋 First-Time Setup Workflow

Follow these steps **once** when first cloning the repository:

### Step 1: Verify Core Tools ✅
All core tools are installed and ready.

### Step 2: Install Recommended Extensions
```powershell
code --install-extension joshrmosier.streamlit-runner
code --install-extension yzhang.markdown-all-in-one
code --install-extension davidanson.vscode-markdownlint
```

### Step 3: Run Setup Script
```powershell
# From repository root
.\setup-beta.ps1
```

### Step 4: Configure API Credentials
1. Open `.env` file created by setup script
2. Add your Spruce Health API credentials
3. Add Microsoft Forms URL (after creating consent form)
4. Save and close

### Step 5: Test Installation
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Test Streamlit
streamlit --version

# Test database connection
python -c "import sys; sys.path.insert(0, 'app'); from database import test_connection; test_connection()"

# Run the app
.\run-app.ps1
```

### Step 6: Verify HIPAA Compliance
- [ ] Confirm BitLocker encryption enabled
- [ ] Review `.gitignore` to ensure PHI files excluded
- [ ] Confirm Spruce Health BAA in place
- [ ] Confirm Microsoft 365 BAA in place

### Step 7: Verify Claude Code Access
```powershell
# Open Copilot Chat in VS Code
# - Press Ctrl+Alt+I (Windows) or Cmd+Alt+I (Mac)
# - Or click the chat icon in the Activity Bar
# - Select "Claude 3.5 Sonnet" from the model picker dropdown
# - Type a test message: "Hello, can you see my workspace context?"
# - Verify you get a response from Claude
```

**Expected Result:** Claude should respond and be able to see files like `CLAUDE.md`, `README.md`, and workspace structure.

**Troubleshooting:**
- If Claude model not available: Ensure GitHub Copilot subscription is active
- If no workspace context: Check that `.github/copilot-instructions.md` exists
- If custom commands don't work: Restart VS Code to reload `.claude/` folder

---

## 🎯 Post-Setup Validation

After completing setup, you should be able to:

- [x] Run `python --version` and see 3.12.2
- [ ] Run `.\.venv\Scripts\Activate.ps1` without errors
- [ ] Run `streamlit --version` from activated venv
- [ ] Run `python -m phase0 test-spruce` (will fail without API keys, but should not crash)
- [ ] Run `streamlit run app/main.py` and see web UI
- [ ] Open workspace in VS Code with all extensions active
- [ ] Open Copilot Chat and select Claude 3.5 Sonnet model
- [ ] Test a custom slash command like `/workspace-brief`

---

## 🔄 Updating This Checklist

**When to update:**
- New developer joining team
- Upgrading Python/Node versions
- Adding new required tools
- Changing API dependencies

**Do not modify** other files in `..Workspace/Settings/` folder unless explicitly documented in `reconciliation-rules.md`.

---

## 📚 Related Documentation

- [README.md](../README.md) - Project overview & quick start
- [CLAUDE.md](../CLAUDE.md) - AI assistant guidance
- [setup-beta.ps1](../setup-beta.ps1) - Automated setup script
- [requirements.txt](../requirements.txt) - Python dependencies
- [docs/planning/alpha-deployment-guide.md](../docs/planning/alpha-deployment-guide.md) - Deployment guide

---

**Last Updated:** December 2, 2025  
**Next Review:** When onboarding new developer or upgrading major dependencies
