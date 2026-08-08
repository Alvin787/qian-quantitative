"""
Utility to download a YouTube livestream recording and transcribe it with
OpenAI's Whisper API.

Example usage (from the repository root):

    python -m backend.utils.youtube_whisper_transcriber \
        "https://www.youtube.com/watch?v=VIDEO_ID"

        python3 -m backend.utils.youtube_whisper_transcriber "https://www.youtube.com/watch?v=Z28JsUUaMVU&t=37302s"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from yt_dlp import YoutubeDL

load_dotenv()

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_WORK_DIR = _BACKEND_ROOT / "data" / "youtube_transcripts"


class YouTubeWhisperTranscriber:
    """Download a YouTube video and transcribe it using OpenAI Whisper."""

    def __init__(
        self,
        *,
        transcripts_dir: Path,
        downloads_dir: Path,
        openai_api_key: str | None = None,
        chunk_seconds: int = 900,
        max_chunk_mb: int = 23,
    ) -> None:
        self.transcripts_dir = transcripts_dir
        self.downloads_dir = downloads_dir
        self.chunk_seconds = chunk_seconds
        self.max_chunk_bytes = max_chunk_mb * 1024 * 1024

        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key missing. Set OPENAI_API_KEY env var or "
                "pass --api-key to the script."
            )

        self.client = OpenAI(api_key=api_key)

    def process_url(self, url: str, *, keep_audio: bool = False) -> Path:
        """Download the audio for a YouTube URL, transcribe, and persist results."""
        audio_path, video_info = self._download_audio(url)
        transcript_text = self._transcribe_audio(audio_path)
        transcript_path = self._store_transcript(transcript_text, video_info, url)

        if not keep_audio:
            try:
                audio_path.unlink()
            except OSError as exc:
                logger.warning("Unable to remove temporary audio %s: %s", audio_path, exc)

        return transcript_path

    def _download_audio(self, url: str) -> Tuple[Path, Dict]:
        """Fetch the best available audio stream for the provided URL."""
        output_template = str(self.downloads_dir / "%(id)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": False,
            "no_warnings": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            download_base = Path(ydl.prepare_filename(info))
            if download_base.exists():
                audio_path = download_base
            else:
                ext = info.get("ext")
                candidate = download_base.with_suffix(f".{ext}") if ext else download_base
                audio_path = candidate if candidate.exists() else download_base

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio download failed; expected file at {audio_path} was not created."
            )

        logger.info("Downloaded audio to %s", audio_path)
        return audio_path, info

    def _transcribe_audio(self, audio_path: Path) -> str:
        """Send the audio file to OpenAI Whisper and return the transcript text."""
        chunk_paths = self._chunk_audio(audio_path)

        transcripts: List[str] = []
        try:
            for index, chunk_path in enumerate(chunk_paths, start=1):
                logger.info(
                    "Submitting chunk %d/%d (%0.2f MB) to Whisper",
                    index,
                    len(chunk_paths),
                    chunk_path.stat().st_size / (1024 * 1024),
                )
                with chunk_path.open("rb") as audio_file:
                    result = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                    )

                text = getattr(result, "text", "")
                if not text:
                    raise RuntimeError(
                        f"Whisper API returned an empty response for chunk {index}."
                    )
                transcripts.append(text.strip())
        finally:
            self._cleanup_chunks(chunk_paths)

        combined = "\n\n".join(transcripts)
        logger.info("Transcription completed (%d characters)", len(combined))
        return combined

    def _store_transcript(self, transcript: str, video_info: Dict, url: str) -> Path:
        """Persist the transcript and related metadata to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = video_info.get("id", "unknown")
        safe_title = _slugify(video_info.get("title") or "")

        transcript_filename = f"{timestamp}_{video_id}_{safe_title}.txt"
        transcript_path = self.transcripts_dir / transcript_filename

        transcript_path.write_text(transcript, encoding="utf-8")

        metadata = {
            "video_id": video_id,
            "title": video_info.get("title"),
            "uploader": video_info.get("uploader"),
            "upload_date": video_info.get("upload_date"),
            "duration": video_info.get("duration"),
            "webpage_url": video_info.get("webpage_url") or url,
            "timestamp": timestamp,
            "audio_filename": video_info.get("_filename"),
        }

        metadata_path = transcript_path.with_suffix(".json")
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        logger.info("Transcript saved to %s", transcript_path)
        logger.info("Metadata saved to %s", metadata_path)

        return transcript_path

    def _chunk_audio(self, audio_path: Path) -> List[Path]:
        """Split large audio files into segments that fit Whisper upload limits."""
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError(
                "ffmpeg is required for chunking audio. Install it (e.g. brew install ffmpeg)."
            )

        chunk_dir = self.downloads_dir / f"{audio_path.stem}_chunks"
        if chunk_dir.exists():
            shutil.rmtree(chunk_dir)
        chunk_dir.mkdir(parents=True, exist_ok=True)

        output_pattern = chunk_dir / f"{audio_path.stem}_%03d.mp3"

        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(audio_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "64k",
            "-f",
            "segment",
            "-segment_time",
            str(self.chunk_seconds),
            str(output_pattern),
        ]

        logger.info("Chunking audio with ffmpeg into %s", chunk_dir)
        subprocess.run(cmd, check=True)

        chunks = sorted(chunk_dir.glob("*.mp3"))
        if not chunks:
            raise RuntimeError("Audio chunking produced no output files.")

        for chunk in chunks:
            if chunk.stat().st_size > self.max_chunk_bytes:
                raise RuntimeError(
                    f"Chunk {chunk.name} exceeds {self.max_chunk_bytes / (1024 * 1024):.2f} MB."
                )

        return chunks

    def _cleanup_chunks(self, chunk_paths: List[Path]) -> None:
        """Remove temporary chunk files that were created for transcription."""
        if not chunk_paths:
            return

        chunk_dir = chunk_paths[0].parent
        for chunk_path in chunk_paths:
            try:
                chunk_path.unlink()
            except OSError as exc:
                logger.warning("Unable to remove chunk %s: %s", chunk_path, exc)

        try:
            chunk_dir.rmdir()
        except OSError:
            # Directory still holds files; leave it for inspection.
            pass


def _slugify(value: str, *, max_length: int = 60) -> str:
    """Generate a filesystem-safe slug derived from the video title."""
    if not value:
        return "video"
    cleaned = re.sub(r"\s+", "_", value.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", cleaned)
    return cleaned[:max_length] or "video"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a YouTube livestream recording and transcribe it with Whisper."
    )
    parser.add_argument("url", help="URL of the published YouTube livestream.")
    parser.add_argument(
        "--work-dir",
        default=str(_DEFAULT_WORK_DIR),
        help="Directory where transcripts and downloads will be stored (default: %(default)s).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Explicit OpenAI API key (otherwise OPENAI_API_KEY env var is used).",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Retain the downloaded audio file after transcription.",
    )
    parser.add_argument(
        "--chunk-seconds",
        type=int,
        default=900,
        help="Approximate length in seconds for each audio chunk sent to Whisper (default: %(default)s).",
    )
    parser.add_argument(
        "--max-chunk-mb",
        type=int,
        default=23,
        help="Hard limit enforced per chunk to stay within Whisper upload constraints (default: %(default)s MB).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    work_dir = Path(args.work_dir).expanduser()
    transcriber = YouTubeWhisperTranscriber(
        transcripts_dir=work_dir,
        downloads_dir=work_dir / "downloads",
        openai_api_key=args.api_key,
        chunk_seconds=args.chunk_seconds,
        max_chunk_mb=args.max_chunk_mb,
    )

    transcript_path = transcriber.process_url(args.url, keep_audio=args.keep_audio)
    print(f"Transcript saved to {transcript_path}")


if __name__ == "__main__":
    main()
