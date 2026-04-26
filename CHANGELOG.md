# Changelog

## v1.1.0

### Added
- Added `--input-transcript` to generate a summary from an existing transcript file
- Added support for `HUGGINGFACEHUB_API_TOKEN` in `.env`
- Automatically maps `HUGGINGFACEHUB_API_TOKEN` to `HF_TOKEN` for Hugging Face compatibility

### Improved
- Summary retry workflow is now cleaner because you can summarize later without re-running transcription
- README updated with summary-only usage and Hugging Face token guidance
- Troubleshooting now includes the OpenAI quota failure flow and retry command

### Behavior
- You can now run:
  - `python transcribe_and_summarize.py --input-transcript ./transcripts/example-transcript.txt`
- Transcript and summary outputs still keep the same naming convention and folder structure

## v1.0.0

### Core Features
- Transcribe `.m4a` audio files into text
- Generate structured summaries from transcripts
- Save outputs automatically into:
  - `/transcripts` → `<filename>-transcript.txt`
  - `/summaries` → `<filename>-summary.md`

### Summary Format
- Summaries follow a consistent structure:
  - **Points discussed**
  - **Important concepts (for further research)**

### Dual Transcription Backends
- Local transcription via `faster-whisper`
- API transcription via OpenAI with `--transcription-backend api`

### Hybrid Pipeline
- Local transcription + OpenAI summarization

### Environment & Security
- Uses `.env` for sensitive data such as `OPENAI_API_KEY`

### CLI Features
- `--transcription-backend local|api`
- `--local-model`
- `--device`
- `--compute-type`
- `--skip-summary`
