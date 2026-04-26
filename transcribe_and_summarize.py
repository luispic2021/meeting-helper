#!/usr/bin/env python3
"""Transcribe an audio file and optionally generate a structured summary.

Default behavior:
- Transcription: local with faster-whisper
- Summary: OpenAI API

Outputs:
- ./transcripts/<audio-name>-transcript.txt
- ./summaries/<audio-name>-summary.md

New in v1.1.0:
- Supports --input-transcript to generate a summary from an existing transcript file
- Supports HUGGINGFACEHUB_API_TOKEN by mapping it to HF_TOKEN for Hugging Face downloads
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

TRANSCRIPTS_DIR = Path("transcripts")
SUMMARIES_DIR = Path("summaries")
DEFAULT_LOCAL_MODEL = "small"
DEFAULT_API_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_SUMMARY_MODEL = "gpt-5-mini"
DEFAULT_ENV_FILE = ".env"

SUMMARY_PROMPT_TEMPLATE = """
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe an audio file and optionally generate a structured summary."
    )
    parser.add_argument(
        "audio_file",
        nargs="?",
        type=Path,
        help="Path to the input audio file (for example: .m4a, .mp3, .wav).",
    )
    parser.add_argument(
        "--input-transcript",
        type=Path,
        help="Path to an existing transcript .txt file. If provided, transcription is skipped and only summary generation runs.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory where ./transcripts and ./summaries will be created.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(DEFAULT_ENV_FILE),
        help="Path to the .env file used for sensitive settings. Default: ./.env",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional ISO language hint such as 'en' or 'es'.",
    )
    parser.add_argument(
        "--transcription-backend",
        choices=["local", "api"],
        default="local",
        help="Use local faster-whisper transcription or OpenAI API transcription. Default: local",
    )
    parser.add_argument(
        "--skip-summary",
        action="store_true",
        help="Only generate the transcript and skip summary creation.",
    )
    parser.add_argument(
        "--local-model",
        default=DEFAULT_LOCAL_MODEL,
        help=(
            "faster-whisper model size/name for local transcription. "
            f"Default: {DEFAULT_LOCAL_MODEL}"
        ),
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Device to use for local transcription. Default: auto",
    )
    parser.add_argument(
        "--compute-type",
        default="default",
        help=(
            "Compute type for faster-whisper local inference, for example: "
            "default, int8, int8_float16, float16. Default: default"
        ),
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="Beam size for local transcription. Default: 5",
    )
    parser.add_argument(
        "--api-transcription-model",
        default=DEFAULT_API_TRANSCRIPTION_MODEL,
        help=(
            "OpenAI model to use when --transcription-backend api is selected. "
            f"Default: {DEFAULT_API_TRANSCRIPTION_MODEL}"
        ),
    )
    parser.add_argument(
        "--summary-model",
        default=DEFAULT_SUMMARY_MODEL,
        help=f"OpenAI model to use for summary generation. Default: {DEFAULT_SUMMARY_MODEL}",
    )

    args = parser.parse_args()

    if not args.audio_file and not args.input_transcript:
        parser.error("You must provide either an audio_file or --input-transcript.")

    if args.audio_file and args.input_transcript:
        parser.error("Provide either an audio_file or --input-transcript, not both.")

    return args


def load_environment(env_file: Path) -> None:
    if load_dotenv is None:
        raise RuntimeError(
            "The 'python-dotenv' package is not installed. Run: pip install -r requirements.txt"
        )

    env_file = env_file.expanduser().resolve()
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=False)
    else:
        load_dotenv(override=False)

    # Hugging Face libraries commonly look for HF_TOKEN, but some users prefer
    # storing the token as HUGGINGFACEHUB_API_TOKEN in .env.
    if not os.getenv("HF_TOKEN") and os.getenv("HUGGINGFACEHUB_API_TOKEN"):
        os.environ["HF_TOKEN"] = os.environ["HUGGINGFACEHUB_API_TOKEN"]


def validate_audio_file(audio_file: Path) -> Path:
    audio_file = audio_file.expanduser().resolve()
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    if not audio_file.is_file():
        raise ValueError(f"Path is not a file: {audio_file}")
    return audio_file


def validate_transcript_file(transcript_file: Path) -> Path:
    transcript_file = transcript_file.expanduser().resolve()
    if not transcript_file.exists():
        raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
    if not transcript_file.is_file():
        raise ValueError(f"Path is not a file: {transcript_file}")
    return transcript_file


def ensure_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file before using OpenAI-based features."
        )


def get_output_paths_from_audio(audio_file: Path, output_root: Path) -> tuple[Path, Path]:
    stem = audio_file.stem
    transcripts_dir = output_root / TRANSCRIPTS_DIR
    summaries_dir = output_root / SUMMARIES_DIR
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = transcripts_dir / f"{stem}-transcript.txt"
    summary_path = summaries_dir / f"{stem}-summary.md"
    return transcript_path, summary_path


def get_summary_path_from_transcript(transcript_file: Path, output_root: Path) -> Path:
    summaries_dir = output_root / SUMMARIES_DIR
    summaries_dir.mkdir(parents=True, exist_ok=True)

    stem = transcript_file.stem
    suffix = "-transcript"
    base_name = stem[:-len(suffix)] if stem.endswith(suffix) else stem
    return summaries_dir / f"{base_name}-summary.md"


def write_text_file(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def get_openai_client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The 'openai' package is not installed. Run: pip install -r requirements.txt"
        ) from exc

    return OpenAI()


def transcribe_audio_api(audio_file: Path, model: str, language: Optional[str]) -> str:
    ensure_api_key()
    client = get_openai_client()

    with audio_file.open("rb") as file_obj:
        response = client.audio.transcriptions.create(
            model=model,
            file=file_obj,
            language=language,
        )

    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Transcription response did not contain text.")
    return text.strip()


def transcribe_audio_local(
    audio_file: Path,
    model_name: str,
    language: Optional[str],
    device: str,
    compute_type: str,
    beam_size: int,
) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "The 'faster-whisper' package is not installed. Run: pip install -r requirements.txt"
        ) from exc

    whisper_kwargs = {"device": device}
    if compute_type != "default":
        whisper_kwargs["compute_type"] = compute_type

    model = WhisperModel(model_name, **whisper_kwargs)
    segments, _info = model.transcribe(
        str(audio_file),
        language=language,
        beam_size=beam_size,
    )

    transcript_parts: list[str] = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            transcript_parts.append(text)

    transcript = " ".join(transcript_parts).strip()
    if not transcript:
        raise RuntimeError("Local transcription returned no text.")
    return transcript


def summarize_transcript(transcript: str, model: str) -> str:
    ensure_api_key()
    client = get_openai_client()

    prompt = SUMMARY_PROMPT_TEMPLATE.format(transcript=transcript)
    response = client.responses.create(
        model=model,
        input=prompt,
    )

    summary_text = getattr(response, "output_text", None)
    if summary_text:
        return summary_text.strip()

    try:
        chunks: list[str] = []
        for item in response.output:
            for content in getattr(item, "content", []):
                text_value = getattr(content, "text", None)
                if text_value:
                    chunks.append(text_value)
        if chunks:
            return "\n".join(chunks).strip()
    except Exception:
        pass

    raise RuntimeError("Summary response did not contain text.")


def read_transcript_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def main() -> int:
    args = parse_args()
    load_environment(args.env_file)

    try:
        if args.input_transcript:
            transcript_file = validate_transcript_file(args.input_transcript)
            transcript = read_transcript_file(transcript_file)
            summary_path = get_summary_path_from_transcript(
                transcript_file=transcript_file,
                output_root=args.output_root.expanduser().resolve(),
            )

            if not transcript:
                raise RuntimeError("Transcript file is empty.")

            if args.skip_summary:
                print("Summary skipped. Existing transcript was not modified.")
                return 0

            summary = summarize_transcript(
                transcript=transcript,
                model=args.summary_model,
            )
            write_text_file(summary_path, summary)
            print(f"Summary saved: {summary_path}")
            return 0

        audio_file = validate_audio_file(args.audio_file)
        transcript_path, summary_path = get_output_paths_from_audio(
            audio_file=audio_file,
            output_root=args.output_root.expanduser().resolve(),
        )

        if args.transcription_backend == "api":
            transcript = transcribe_audio_api(
                audio_file=audio_file,
                model=args.api_transcription_model,
                language=args.language,
            )
        else:
            transcript = transcribe_audio_local(
                audio_file=audio_file,
                model_name=args.local_model,
                language=args.language,
                device=args.device,
                compute_type=args.compute_type,
                beam_size=args.beam_size,
            )

        write_text_file(transcript_path, transcript)
        print(f"Transcript saved: {transcript_path}")

        if args.skip_summary:
            print("Summary skipped by request.")
            return 0

        summary = summarize_transcript(
            transcript=transcript,
            model=args.summary_model,
        )
        write_text_file(summary_path, summary)
        print(f"Summary saved: {summary_path}")
        return 0

    except Exception as exc:
        # If summary fails after transcript succeeded, the transcript is still preserved.
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
