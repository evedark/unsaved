#!/usr/bin/env python3
"""Transcribe audio from a video URL with yt-dlp and faster-whisper.

Usage:
    python scripts/transcribe_url.py <url> [--model medium] [--timestamps]
"""
import os
import sys
import tempfile


def check_dependencies() -> None:
    missing = []
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        missing.append("yt-dlp")
    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError:
        missing.append("faster-whisper")

    import shutil
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")

    if missing:
        print("ERROR: Missing dependencies: " + ", ".join(missing), file=sys.stderr)
        pip_packages = [pkg for pkg in missing if pkg != "ffmpeg"]
        if pip_packages:
            print("Install Python packages:", file=sys.stderr)
            print("  python -m pip install " + " ".join(pip_packages), file=sys.stderr)
        if "ffmpeg" in missing:
            print("Install ffmpeg:", file=sys.stderr)
            print("  brew install ffmpeg", file=sys.stderr)
            print("  sudo apt install ffmpeg", file=sys.stderr)
        sys.exit(1)


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def download_audio(url: str, output_dir: str):
    import yt_dlp

    opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "0",
        }],
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.join(output_dir, f"{info['id']}.wav"), info


def transcribe_audio(audio_path: str, model_size: str):
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(audio_path, beam_size=5)
    segments = []
    for segment in segments_iter:
        segments.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "start_formatted": format_timestamp(segment.start),
        })
    return segments, info


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/transcribe_url.py <url> [--model medium] [--timestamps]")

    url = sys.argv[1]
    model_size = "medium"
    show_timestamps = False
    args = sys.argv[2:]

    if "--model" in args:
        index = args.index("--model")
        if index + 1 < len(args):
            model_size = args[index + 1]
    if "--timestamps" in args:
        show_timestamps = True

    check_dependencies()

    tmp_dir = tempfile.mkdtemp()
    try:
        print("Downloading audio...", file=sys.stderr)
        audio_path, video_info = download_audio(url, tmp_dir)

        title = video_info.get("title", "Unknown")
        duration = video_info.get("duration", 0)
        platform = video_info.get("extractor", "Unknown")
        uploader = video_info.get("uploader", "Unknown")

        print(f"Transcribing with {model_size} model...", file=sys.stderr)
        segments, trans_info = transcribe_audio(audio_path, model_size)

        print(f"--- {platform} | {title} | {uploader} | {format_timestamp(duration or trans_info.duration)} ---")
        print()

        if show_timestamps:
            for segment in segments:
                print(f"[{segment['start_formatted']}] {segment['text']}")
        else:
            paragraphs = []
            current = []
            start = 0
            for segment in segments:
                current.append(segment["text"])
                if segment["start"] - start >= 30:
                    paragraphs.append(" ".join(current))
                    current = []
                    start = segment["start"]
            if current:
                paragraphs.append(" ".join(current))
            print("\n\n".join(paragraphs))

        print(
            f"\n--- Transcription complete | {len(segments)} segments | Language: {trans_info.language} ---",
            file=sys.stderr,
        )
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
