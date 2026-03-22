#!/usr/bin/env python3
"""Transcribe an audio file and generate a structured summary.

Supports two transcription backends:
- local: faster-whisper
- api: OpenAI API

Supports summary generation with OpenAI API.

Configuration priority:
1. CLI arguments
2. config.yaml
3. Built-in defaults
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

DEFAULT_ENV_FILE = ".env"
DEFAULT_CONFIG_FILE = "config.yaml"
DEFAULT_API_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_SUMMARY_MODEL = "gpt-5-mini"

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


DEFAULT_CONFIG: dict[str, Any] = {
    "transcription": {
        "backend": "local",
        "local_model": "small",
        "device": "auto",
        "compute_type": "default",
        "beam_size": 5,
        "api_model": DEFAULT_API_TRANSCRIPTION_MODEL,
    },
    "summary": {
        "enabled": True,
        "model": DEFAULT_SUMMARY_MODEL,
    },
    "output": {
        "root_dir": ".",
        "transcripts_dir": "transcripts",
        "summaries_dir": "summaries",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe an audio file and optionally generate a structured summary."
    )
    parser.add_argument(
        "audio_file",
        type=Path,
        help="Path to the input audio file (for example: .m4a, .mp3, .wav).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(DEFAULT_CONFIG_FILE),
        help=f"Path to config YAML file. Default: ./{DEFAULT_CONFIG_FILE}",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(DEFAULT_ENV_FILE),
        help=f"Path to the .env file. Default: ./{DEFAULT_ENV_FILE}",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional ISO language hint such as 'en' or 'es'.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Override output root directory.",
    )
    parser.add_argument(
        "--transcripts-dir",
        default=None,
        help="Override transcript output directory name or path.",
    )
    parser.add_argument(
        "--summaries-dir",
        default=None,
        help="Override summary output directory name or path.",
    )
    parser.add_argument(
        "--transcription-backend",
        choices=["local", "api"],
        default=None,
        help="Transcription backend to use.",
    )
    parser.add_argument(
        "--skip-summary",
        action="store_true",
        help="Only generate the transcript and skip summary creation.",
    )
    parser.add_argument(
        "--local-model",
        default=None,
        help="faster-whisper model size/name for local transcription.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default=None,
        help="Device to use for local transcription.",
    )
    parser.add_argument(
        "--compute-type",
        default=None,
        help="Compute type for faster-whisper local inference.",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=None,
        help="Beam size for local transcription.",
    )
    parser.add_argument(
        "--api-transcription-model",
        default=None,
        help="OpenAI model to use for API transcription.",
    )
    parser.add_argument(
        "--summary-model",
        default=None,
        help="OpenAI model to use for summary generation.",
    )
    return parser.parse_args()


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


def load_config(config_path: Path) -> dict[str, Any]:
    config_path = config_path.expanduser().resolve()
    if not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("config.yaml must contain a top-level mapping/object.")

    return data


def nested_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def resolve_settings(args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any]:
    output_root_value = args.output_root or nested_get(
        config, "output", "root_dir", default=DEFAULT_CONFIG["output"]["root_dir"]
    )
    transcripts_dir_value = args.transcripts_dir or nested_get(
        config,
        "output",
        "transcripts_dir",
        default=DEFAULT_CONFIG["output"]["transcripts_dir"],
    )
    summaries_dir_value = args.summaries_dir or nested_get(
        config,
        "output",
        "summaries_dir",
        default=DEFAULT_CONFIG["output"]["summaries_dir"],
    )

    return {
        "language": args.language,
        "transcription_backend": args.transcription_backend
        or nested_get(
            config,
            "transcription",
            "backend",
            default=DEFAULT_CONFIG["transcription"]["backend"],
        ),
        "local_model": args.local_model
        or nested_get(
            config,
            "transcription",
            "local_model",
            default=DEFAULT_CONFIG["transcription"]["local_model"],
        ),
        "device": args.device
        or nested_get(
            config,
            "transcription",
            "device",
            default=DEFAULT_CONFIG["transcription"]["device"],
        ),
        "compute_type": args.compute_type
        or nested_get(
            config,
            "transcription",
            "compute_type",
            default=DEFAULT_CONFIG["transcription"]["compute_type"],
        ),
        "beam_size": args.beam_size
        or int(
            nested_get(
                config,
                "transcription",
                "beam_size",
                default=DEFAULT_CONFIG["transcription"]["beam_size"],
            )
        ),
        "api_transcription_model": args.api_transcription_model
        or nested_get(
            config,
            "transcription",
            "api_model",
            default=DEFAULT_CONFIG["transcription"]["api_model"],
        ),
        "summary_enabled": (
            False
            if args.skip_summary
            else bool(
                nested_get(
                    config,
                    "summary",
                    "enabled",
                    default=DEFAULT_CONFIG["summary"]["enabled"],
                )
            )
        ),
        "summary_model": args.summary_model
        or nested_get(
            config,
            "summary",
            "model",
            default=DEFAULT_CONFIG["summary"]["model"],
        ),
        "output_root": Path(output_root_value),
        "transcripts_dir": Path(transcripts_dir_value),
        "summaries_dir": Path(summaries_dir_value),
    }


def validate_audio_file(audio_file: Path) -> Path:
    audio_file = audio_file.expanduser().resolve()
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    if not audio_file.is_file():
        raise ValueError(f"Path is not a file: {audio_file}")
    return audio_file


def ensure_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file before using OpenAI-based features."
        )


def resolve_output_dir(root: Path, child: Path) -> Path:
    return child if child.is_absolute() else root / child


def get_output_paths(
    audio_file: Path,
    output_root: Path,
    transcripts_dir: Path,
    summaries_dir: Path,
) -> tuple[Path, Path]:
    stem = audio_file.stem
    transcripts_path = resolve_output_dir(output_root, transcripts_dir)
    summaries_path = resolve_output_dir(output_root, summaries_dir)
    transcripts_path.mkdir(parents=True, exist_ok=True)
    summaries_path.mkdir(parents=True, exist_ok=True)

    transcript_file = transcripts_path / f"{stem}-transcript.txt"
    summary_file = summaries_path / f"{stem}-summary.md"
    return transcript_file, summary_file


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
        kwargs: dict[str, Any] = {
            "model": model,
            "file": file_obj,
        }
        if language:
            kwargs["language"] = language

        response = client.audio.transcriptions.create(**kwargs)

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

    whisper_kwargs: dict[str, Any] = {"device": device}
    if compute_type != "default":
        whisper_kwargs["compute_type"] = compute_type

    model = WhisperModel(model_name, **whisper_kwargs)
    transcribe_kwargs: dict[str, Any] = {
        "beam_size": beam_size,
    }
    if language:
        transcribe_kwargs["language"] = language

    segments, _info = model.transcribe(str(audio_file), **transcribe_kwargs)

    transcript_parts: list[str] = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            transcript_parts.append(text)

    transcript = " ".join(transcript_parts).strip()
    if not transcript:
        raise RuntimeError(
            "Local transcription returned no text. Verify the audio file and that ffmpeg is installed."
        )
    return transcript


def summarize_transcript(transcript: str, model: str) -> str:
    ensure_api_key()
    client = get_openai_client()
    prompt = SUMMARY_PROMPT_TEMPLATE.format(transcript=transcript)

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    output_text = getattr(response, "output_text", "")
    if output_text:
        return output_text.strip()

    raise RuntimeError("Summary response did not contain output_text.")


def main() -> int:
    args = parse_args()
    load_environment(args.env_file)
    config = load_config(args.config)
    settings = resolve_settings(args, config)

    audio_file = validate_audio_file(args.audio_file)
    transcript_path, summary_path = get_output_paths(
        audio_file=audio_file,
        output_root=settings["output_root"],
        transcripts_dir=settings["transcripts_dir"],
        summaries_dir=settings["summaries_dir"],
    )

    if settings["transcription_backend"] == "api":
        transcript = transcribe_audio_api(
            audio_file=audio_file,
            model=settings["api_transcription_model"],
            language=settings["language"],
        )
    else:
        transcript = transcribe_audio_local(
            audio_file=audio_file,
            model_name=settings["local_model"],
            language=settings["language"],
            device=settings["device"],
            compute_type=settings["compute_type"],
            beam_size=settings["beam_size"],
        )

    write_text_file(transcript_path, transcript)
    print(f"Transcript saved to: {transcript_path}")

    if settings["summary_enabled"]:
        summary = summarize_transcript(
            transcript=transcript,
            model=settings["summary_model"],
        )
        write_text_file(summary_path, summary)
        print(f"Summary saved to: {summary_path}")
    else:
        print("Summary generation skipped.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
