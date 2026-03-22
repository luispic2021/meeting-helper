# Changelog

## v1.0.0 — Initial Release

### 🎯 Core Features
- Transcribe `.m4a` audio files into text
- Generate structured summaries from transcripts
- Save outputs automatically into:
  - `/transcripts` → `<filename>-transcript.txt`
  - `/summaries` → `<filename>-summary.md`

### 🧠 Summary Format
- Summaries follow a consistent structure:
  - **Points discussed**
  - **Important concepts (for further research)**

### ⚙️ Dual Transcription Backends
- **Local transcription** via `faster-whisper`
  - Runs fully offline
  - Supports CPU/GPU and quantization options
- **API transcription** via OpenAI
  - Simple, no local setup required
  - Enabled with `--transcription-backend api`

### 🔄 Hybrid Pipeline (Recommended)
- Local transcription + OpenAI summarization
- Balances privacy, cost, and quality

### 🔐 Environment & Security
- Uses `.env` for sensitive data (e.g., `OPENAI_API_KEY`)
- No hardcoded credentials
- Compatible with `.venv` workflow

### ⚙️ Configuration System
- Introduced `config.yaml` for default behavior
- Configurable options:
  - transcription backend (local/api)
  - local model settings (model size, device, compute type)
  - summary model
  - output directories
- CLI flags override config values

### 🧩 CLI Features
- `--transcription-backend local|api`
- `--local-model`
- `--device`
- `--compute-type`
- `--skip-summary`

### 📦 Project Structure
- Clean separation of:
  - transcripts
  - summaries
  - config
  - environment variables

### 🚀 Usability
- Works out-of-the-box with minimal setup
- Supports both fully local and cloud-powered workflows
- Easily extensible for future features (e.g., local LLM summaries)
