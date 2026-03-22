#!/usr/bin/env python3
"""Transcribe an audio file and generate a markdown summary.

Usage:
    python transcribe_and_summarize.py /path/to/audio.m4a

Outputs:
    ./transcripts/<audio-name>-transcript.txt
    ./summaries/<audio-name>-summary.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from openai import OpenAI

TRANSCRIPTS_DIR = Path("transcripts")
SUMMARIES_DIR = Path("summaries")
DEFAULT_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_SUMMARY_MODEL = "gpt-5-mini"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe an audio file and generate a structured summary."
    )
    parser.add_argument(
        "audio_file",
        type=Path,
        help="Path to the input audio file (for example: .m4a, .mp3, .wav).",
    )
    parser.add_argument(
        "--transcription-model",
        default=DEFAULT_TRANSCRIPTION_MODEL,
        help=f"OpenAI transcription model to use. Default: {DEFAULT_TRANSCRIPTION_MODEL}",
    )
    parser.add_argument(
        "--summary-model",
        default=DEFAULT_SUMMARY_MODEL,
        help=f"OpenAI model to use for summary generation. Default: {DEFAULT_SUMMARY_MODEL}",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional ISO language hint such as 'en' or 'es'.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory where ./transcripts and ./summaries will be created. Default: current directory.",
    )
    return parser.parse_args()


def ensure_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export your API key before running the script."
        )


def validate_audio_file(audio_file: Path) -> Path:
    audio_file = audio_file.expanduser().resolve()
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    if not audio_file.is_file():
        raise ValueError(f"Path is not a file: {audio_file}")
    return audio_file


def get_output_paths(audio_file: Path, output_root: Path) -> tuple[Path, Path]:
    stem = audio_file.stem
    transcripts_dir = output_root / TRANSCRIPTS_DIR
    summaries_dir = output_root / SUMMARIES_DIR
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = transcripts_dir / f"{stem}-transcript.txt"
    summary_path = summaries_dir / f"{stem}-summary.md"
    return transcript_path, summary_path


def transcribe_audio(
    client: OpenAI,
    audio_file: Path,
    model: str,
    language: str | None = None,
) -> str:
    with audio_file.open("rb") as f:
        response = client.audio.transcriptions.create(
            model=model,
            file=f,
            language=language,
        )

    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Transcription response did not contain text.")
    return text.strip()


def summarize_transcript(client: OpenAI, transcript: str, model: str) -> str:
    prompt = f"""
You are summarizing a transcript from an audio conversation.

Create a concise markdown summary using exactly these section headers:

# Points discussed
# Important concepts (for further research)

Rules:
- Use bullet points under each heading.
- Keep the content grounded in the transcript only.
- Do not invent names, facts, decisions, or action items.
- In "Important concepts (for further research)", include terms, frameworks, companies, tools, or ideas that were mentioned or clearly implied and would benefit from follow-up.
- If a section has no meaningful content, include a bullet that says "None clearly identified.".

Transcript:
{transcript}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    summary_text = getattr(response, "output_text", None)
    if not summary_text:
        raise RuntimeError("Summary response did not contain output_text.")
    return summary_text.strip()


def write_text_file(path: Path, content: str) -> None:
    path.write_text(content + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    try:
        ensure_api_key()
        audio_file = validate_audio_file(args.audio_file)
        output_root = args.output_root.expanduser().resolve()
        transcript_path, summary_path = get_output_paths(audio_file, output_root)

        client = OpenAI()

        print(f"Transcribing: {audio_file}")
        transcript = transcribe_audio(
            client=client,
            audio_file=audio_file,
            model=args.transcription_model,
            language=args.language,
        )
        write_text_file(transcript_path, transcript)
        print(f"Saved transcript to: {transcript_path}")

        print("Generating summary...")
        summary = summarize_transcript(
            client=client,
            transcript=transcript,
            model=args.summary_model,
        )
        write_text_file(summary_path, summary)
        print(f"Saved summary to: {summary_path}")

        print("Done.")
        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
