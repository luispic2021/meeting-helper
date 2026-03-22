# Audio Transcriber + Conversation Summarizer

This project transcribes an audio file such as `.m4a` and saves:

- a plain-text transcript in `./transcripts/`
- a markdown summary in `./summaries/`

## Output format

Given an input file like `meeting.m4a`, the script creates:

- `./transcripts/meeting-transcript.txt`
- `./summaries/meeting-summary.md`

The summary uses exactly these sections:

- `# Points discussed`
- `# Important concepts (for further research)`

## Default behavior

By default, the script uses a hybrid setup:

- **Transcription:** local with `faster-whisper`
- **Summary:** OpenAI API

This keeps the raw audio local while still using a hosted model for the summary.

## Project files

- `transcribe_and_summarize.py`
- `config.yaml`
- `requirements.txt`
- `.env.example`
- `README.md`

## Requirements

- Python 3.10+
- `ffmpeg` installed on your system for local audio decoding
- An OpenAI API key in `.env` only if you want summaries or API-based transcription

## Setup

### 1) Create and activate your virtual environment

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3) Install ffmpeg

#### macOS with Homebrew

```bash
brew install ffmpeg
```

#### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y ffmpeg
```

#### Windows

Install `ffmpeg` and make sure it is available on your `PATH`.

### 4) Create your `.env` file

Copy `.env.example` to `.env` and add your key only if you plan to use OpenAI-powered steps.

```bash
cp .env.example .env
```

Then edit `.env`:

```env
OPENAI_API_KEY=your_api_key_here
```

### 5) Review `config.yaml`

This file sets the default behavior for the script.

```yaml
transcription:
  backend: local
  local_model: small
  device: auto
  compute_type: default
  beam_size: 5
  api_model: gpt-4o-mini-transcribe

summary:
  enabled: true
  model: gpt-5-mini

output:
  root_dir: .
  transcripts_dir: transcripts
  summaries_dir: summaries
```

## Configuration priority

The script resolves settings in this order:

1. CLI arguments
2. `config.yaml`
3. built-in defaults

That means you can keep a sane default in `config.yaml` and override it when needed.

## Usage

### Default: local transcript + OpenAI summary

```bash
python transcribe_and_summarize.py /path/to/audio.m4a
```

### Only create a local transcript

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --skip-summary
```

### Force OpenAI API for transcription too

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --transcription-backend api
```

### Provide a language hint

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --language en
```

### Override the local Whisper model

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --local-model medium
```

### Override the output root

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --output-root /path/to/output
```

### Override config values for one run

```bash
python transcribe_and_summarize.py /path/to/audio.m4a \
  --transcription-backend api \
  --summary-model gpt-5-mini
```

## API vs local transcription

If you run with:

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --transcription-backend api
```

you do **not** need any local Whisper model setup.

That means you can skip local model downloads entirely and use OpenAI for both:

- transcription
- summary

You still need `OPENAI_API_KEY` in `.env` for that mode.

## Recommended local model sizes

- `tiny`: fastest, lowest accuracy
- `base`: light and quick
- `small`: good default balance
- `medium`: better quality, slower
- `large-v3`: best quality, heaviest

## Troubleshooting

### `OPENAI_API_KEY is not set`

Add it to `.env` before using summary generation or API transcription.

### `Local transcription returned no text`

Check that:

- the file really contains speech
- `ffmpeg` is installed and available on your `PATH`
- the chosen model is appropriate for your machine

### `No module named faster_whisper`

Reinstall dependencies:

```bash
pip install -r requirements.txt
```

### Local transcription is too slow

Try one of these:

- change `local_model` to `base`
- change `compute_type` to `int8`
- use `device: cuda` if you have a supported NVIDIA GPU
- temporarily switch to `--transcription-backend api`

## Example workflows

### Hybrid mode from config

```bash
python transcribe_and_summarize.py ./audio/meeting.m4a
```

### Local transcript only

```bash
python transcribe_and_summarize.py ./audio/meeting.m4a --skip-summary --local-model base
```

### API transcript + API summary

```bash
python transcribe_and_summarize.py ./audio/meeting.m4a --transcription-backend api
```
