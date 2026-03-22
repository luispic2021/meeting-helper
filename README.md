# Audio Transcriber + Conversation Summarizer

This project transcribes an audio file (including `.m4a`) and then creates a structured summary.

## What it creates

Given an input file like:

`meeting.m4a`

the script will create:

- `./transcripts/meeting-transcript.txt`
- `./summaries/meeting-summary.md`

## Summary format

The summary is generated in markdown with exactly these sections:

- `# Points discussed`
- `# Important concepts (for further research)`

## Requirements

- Python 3.10+
- An OpenAI API key

## Setup

1. Create and activate a virtual environment.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your API key.

### macOS / Linux

```bash
export OPENAI_API_KEY="your_api_key_here"
```

### Windows (PowerShell)

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

## Usage

Run the script with the path to your audio file:

```bash
python transcribe_and_summarize.py /path/to/your/audio.m4a
```

Optional arguments:

```bash
python transcribe_and_summarize.py /path/to/audio.m4a \
  --language en \
  --output-root /path/to/output
```

## Output folders

The script automatically creates these folders under the output root:

- `transcripts/`
- `summaries/`

By default, the output root is your current working directory.

## Example

If you run:

```bash
python transcribe_and_summarize.py ./audio/client-call.m4a
```

you will get:

- `./transcripts/client-call-transcript.txt`
- `./summaries/client-call-summary.md`

## Notes

- The script uses the OpenAI audio transcription endpoint for transcription and an OpenAI text model for summarization.
- The transcription is saved as plain text for easy reuse.
- The summary is saved as markdown for easier reading.
- The script is designed for single-file processing.

## Model defaults

- Transcription model: `gpt-4o-mini-transcribe`
- Summary model: `gpt-5-mini`

You can override both with command-line flags:

```bash
python transcribe_and_summarize.py yourfile.m4a \
  --transcription-model gpt-4o-mini-transcribe \
  --summary-model gpt-5-mini
```

## Troubleshooting

### `OPENAI_API_KEY is not set`

Make sure your environment variable is exported in the same shell session where you run the script.

### `Audio file not found`

Double-check the input path and filename.

### Empty or weak summaries

Try providing the `--language` flag when the audio is mostly in a single language.
