# Audio Transcriber + Conversation Summarizer

This project transcribes an audio file such as `.m4a` and saves:

- a plain-text transcript in `./transcripts/`
- a markdown summary in `./summaries/`

It also supports generating a summary later from an existing transcript file, so you do not need to re-run transcription if your summary step fails or your API account is not funded yet.

## Output format

Given an input file like `meeting.m4a`, the script creates:

- `./transcripts/meeting-transcript.txt`
- `./summaries/meeting-summary.md`

If you summarize from an existing transcript like:

- `./transcripts/meeting-transcript.txt`

the script creates:

- `./summaries/meeting-summary.md`

The summary uses exactly these sections:

- `# Points discussed`
- `# Important concepts (for further research)`

## Default behavior

By default, the script uses a hybrid setup:

- **Transcription:** local with `faster-whisper`
- **Summary:** OpenAI API

This keeps the raw audio local while still using a hosted model for the summary.

## Requirements

- Python 3.10+
- `ffmpeg` installed on your system for local audio decoding
- An OpenAI API key in `.env` **only if** you want summaries or API-based transcription
- Optional Hugging Face token in `.env` for higher rate limits and smoother local model downloads

## Project files

- `transcribe_and_summarize.py`
- `requirements.txt`
- `README.md`

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

### 4) Create a `.env` file for sensitive data

Create a file named `.env` in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
```

Notes:
- `OPENAI_API_KEY` is only required for OpenAI summary generation or API-based transcription.
- `HUGGINGFACEHUB_API_TOKEN` is optional, but recommended if you use local transcription and want better Hugging Face download behavior.
- The script maps `HUGGINGFACEHUB_API_TOKEN` to `HF_TOKEN` automatically for compatibility with Hugging Face tooling.

The script loads `.env` automatically. You can also point to a different file with `--env-file`.

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

### Generate summary only from an existing transcript

```bash
python transcribe_and_summarize.py --input-transcript ./transcripts/meeting-transcript.txt
```

This is useful when:
- local transcription already succeeded
- summary failed because your OpenAI account had no quota
- you want to retry only the summary step later

### Provide a language hint

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --language en
```

### Change the local Whisper model

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --local-model medium
```

### Write output somewhere else

```bash
python transcribe_and_summarize.py /path/to/audio.m4a --output-root /path/to/output
```

## Recommended local model sizes

These are practical starting points:

- `tiny`: fastest, lowest accuracy
- `base`: light and quick
- `small`: good default balance
- `medium`: better quality, slower
- `large-v3`: best quality, heaviest

Example:

```bash
python transcribe_and_summarize.py ./audio/client-call.m4a --local-model small
```

## OpenAI-related defaults

- API transcription model: `gpt-4o-mini-transcribe`
- Summary model: `gpt-5-mini`

You can override them:

```bash
python transcribe_and_summarize.py yourfile.m4a \
  --transcription-backend api \
  --api-transcription-model gpt-4o-mini-transcribe \
  --summary-model gpt-5-mini
```

## Notes

- The transcript is saved as `.txt` for easy reuse.
- The summary is saved as `.md` for easier reading.
- If you skip the summary, the script does not require `OPENAI_API_KEY` unless you also selected API transcription.
- `faster-whisper` may download the selected local model the first time you run it.
- The Hugging Face token is optional for local transcription, but helps avoid anonymous rate limits and slower downloads.

## Troubleshooting

### `OPENAI_API_KEY is not set`

Add it to your `.env` file before running any OpenAI-powered step.

### `Error code: 429 ... insufficient_quota`

Your transcript can still be preserved if transcription already finished.

Once your OpenAI account is funded, run summary-only mode:

```bash
python transcribe_and_summarize.py --input-transcript ./transcripts/meeting-transcript.txt
```

### Hugging Face warning about unauthenticated requests

Add this to your `.env`:

```env
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
```

The script will map it to `HF_TOKEN` automatically.

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
- use `--local-model base`
- use `--compute-type int8`
- use `--device cuda` if you have a supported NVIDIA GPU

## Example end-to-end commands

### Hybrid mode

```bash
python transcribe_and_summarize.py ./audio/meeting.m4a
```

### Local transcript only

```bash
python transcribe_and_summarize.py ./audio/meeting.m4a --skip-summary --local-model base
```

### Retry summary later from saved transcript

```bash
python transcribe_and_summarize.py --input-transcript ./transcripts/meeting-transcript.txt
```

### API transcript + API summary

```bash
python transcribe_and_summarize.py ./audio/meeting.m4a --transcription-backend api
```
